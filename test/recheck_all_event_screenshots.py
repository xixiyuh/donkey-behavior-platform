import sys
import sqlite3
from pathlib import Path

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "data" / "farm.db"
MODEL_PATH = PROJECT_ROOT / "models" / "contract-best.pt"


def resize_with_padding(img, target_size=(224, 224)):
    width, height = img.size
    target_width, target_height = target_size

    scale = min(target_width / width, target_height / height)
    new_width = int(width * scale)
    new_height = int(height * scale)

    img = img.resize((new_width, new_height), Image.BILINEAR)

    padded_img = Image.new("RGB", target_size, (0, 0, 0))
    paste_x = (target_width - new_width) // 2
    paste_y = (target_height - new_height) // 2
    padded_img.paste(img, (paste_x, paste_y))
    return padded_img


class CheckpointCompatibleModel(nn.Module):
    def __init__(self):
        super().__init__()

        base = models.resnet18(weights=None)

        # 对齐 checkpoint 里的 features.*
        self.features = nn.Sequential(*list(base.children())[:-1])  # [B, 512, 1, 1]

        # 对齐 checkpoint 里的 attention.*
        self.attention = nn.Sequential(
            nn.Conv2d(512, 64, kernel_size=1, stride=1, padding=0),
            nn.ReLU(),
            nn.Conv2d(64, 1, kernel_size=1, stride=1, padding=0),
            nn.Sigmoid(),
        )

        # 对齐 checkpoint 里的 classifier.*
        self.classifier = nn.Sequential(
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.5),

            nn.Linear(256, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.5),

            nn.Linear(64, 1),
        )

    def forward(self, x):
        feats = self.features(x)               # [B, 512, 1, 1]
        attn = self.attention(feats)           # [B, 1, 1, 1]
        feats = feats * attn                   # [B, 512, 1, 1]
        feats = feats.view(feats.size(0), -1) # [B, 512]
        logits = self.classifier(feats)        # [B, 1]
        return logits, feats


def load_model_and_threshold(model_path, device):
    ckpt = torch.load(model_path, map_location=device, weights_only=False)
    state = ckpt["model_state_dict"]

    model = CheckpointCompatibleModel().to(device)

    filtered_state = {
        k: v for k, v in state.items()
        if k.startswith("features.") or k.startswith("classifier.") or k.startswith("attention.")
    }

    missing, unexpected = model.load_state_dict(filtered_state, strict=False)

    threshold = ckpt.get("threshold", 0.5)

    print("模型加载完成")
    print(f"threshold = {threshold}")
    print(f"missing keys = {missing}")
    print(f"unexpected keys = {unexpected}")

    model.eval()
    return model, threshold


def resolve_image_path(screenshot: str) -> Path:
    return PROJECT_ROOT / screenshot.lstrip("/")


def main():
    print(f"数据库路径: {DB_PATH}")
    print(f"数据库是否存在: {DB_PATH.exists()}")
    print(f"模型路径: {MODEL_PATH}")
    print(f"模型是否存在: {MODEL_PATH.exists()}")

    if not DB_PATH.exists():
        print("数据库不存在，脚本结束")
        return

    if not MODEL_PATH.exists():
        print("模型不存在，脚本结束")
        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, threshold = load_model_and_threshold(MODEL_PATH, device)

    transform = transforms.Compose([
        transforms.Lambda(lambda img: resize_with_padding(img, (224, 224))),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, camera_id, start_time, end_time, avg_confidence, screenshot
        FROM mating_events
        WHERE screenshot IS NOT NULL AND screenshot != ''
        ORDER BY id
    """)
    rows = cursor.fetchall()
    conn.close()

    print(f"共读取到 {len(rows)} 条带截图的事件")

    mating_ids = []
    non_mating_ids = []
    missing_ids = []
    error_ids = []

    for row in rows:
        event_id, camera_id, start_time, end_time, avg_confidence, screenshot = row
        img_path = resolve_image_path(screenshot)

        if not img_path.exists():
            print(f"[图片不存在] id={event_id}, path={img_path}")
            missing_ids.append(event_id)
            continue

        try:
            img = Image.open(img_path).convert("RGB")
            x = transform(img).unsqueeze(0).to(device)

            with torch.no_grad():
                logits, _ = model(x)
                score = torch.sigmoid(logits.squeeze(-1)).item()

            pred_label = 1 if score >= threshold else 0
            pred_name = "Mating" if pred_label == 1 else "Non-Mating"

            if pred_label == 1:
                mating_ids.append(event_id)
            else:
                non_mating_ids.append(event_id)

            print(
                f"[检测完成] id={event_id}, camera_id={camera_id}, "
                f"result={pred_name}, score={score:.6f}, threshold={threshold:.6f}, file={img_path.name}"
            )

        except Exception as e:
            print(f"[检测失败] id={event_id}, path={img_path}, error={e}")
            error_ids.append(event_id)

    print("\n========== 重检完成 ==========")
    print(f"Mating 数量: {len(mating_ids)}")
    print(f"Mating 事件id: {mating_ids}")

    print(f"\nNon-Mating 数量: {len(non_mating_ids)}")
    print(f"Non-Mating 事件id: {non_mating_ids}")

    print(f"\n图片不存在数量: {len(missing_ids)}")
    print(f"图片不存在事件id: {missing_ids}")

    print(f"\n检测失败数量: {len(error_ids)}")
    print(f"检测失败事件id: {error_ids}")


if __name__ == "__main__":
    main()