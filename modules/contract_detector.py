# modules/contract_detector.py
import os
import torch
from torchvision import transforms
from PIL import Image, ImageFile
from .config import CONTRACT_MODEL_PATH
import warnings

ImageFile.LOAD_TRUNCATED_IMAGES = True
warnings.filterwarnings("ignore")

# 定义FeatureExtractorResNet类
import torch.nn as nn
from torchvision import models

class FeatureExtractorResNet(nn.Module):
    def __init__(self, pretrained=True):
        super(FeatureExtractorResNet, self).__init__()
        # 使用ResNet18作为特征提取器
        self.resnet = models.resnet18(pretrained=pretrained)
        # 移除最后的全连接层
        self.resnet = nn.Sequential(*list(self.resnet.children())[:-1])
        
        # 添加分类头
        self.fc = nn.Linear(512, 1)
        
    def forward(self, x):
        # 特征提取
        features = self.resnet(x)
        features = features.view(features.size(0), -1)
        
        # 分类
        output = self.fc(features)
        
        return output, features


def _resize_with_padding(img, target_size):
    """
    等比例缩放图像，然后填充到目标尺寸
    与训练/评估时保持一致
    """
    width, height = img.size
    target_width, target_height = target_size

    scale_w = target_width / width
    scale_h = target_height / height
    scale = min(scale_w, scale_h)

    new_width = int(width * scale)
    new_height = int(height * scale)

    img = img.resize((new_width, new_height), Image.BILINEAR)

    padded_img = Image.new("RGB", target_size, (0, 0, 0))
    paste_x = (target_width - new_width) // 2
    paste_y = (target_height - new_height) // 2
    padded_img.paste(img, (paste_x, paste_y))

    return padded_img


def load_model_and_threshold(model_path, device):
    print(f"加载模型: {model_path}")
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)

    model = FeatureExtractorResNet(pretrained=False).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    threshold = checkpoint.get("threshold", 0.5)
    print(f"模型加载成功，最佳阈值: {threshold:.4f}")

    return model, threshold


class ContractDetector:
    def __init__(self, model_path):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model, self.threshold = load_model_and_threshold(model_path, self.device)
        self.transform = transforms.Compose([
            transforms.Lambda(lambda img: _resize_with_padding(img, (224, 224))),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

    def predict(self, image_path):
        """
        预测单张图片
        返回: True if mating, False otherwise
        """
        try:
            img = Image.open(image_path).convert("RGB")
            img_tensor = self.transform(img).unsqueeze(0).to(self.device)  # [1, 3, 224, 224]

            with torch.no_grad():
                outputs, _ = self.model(img_tensor)

                if outputs.dim() > 1:
                    score = torch.sigmoid(outputs.squeeze(-1)).item()
                else:
                    score = torch.sigmoid(outputs).item()

            pred_label = 1 if score >= self.threshold else 0
            pred_name = "Mating" if pred_label == 1 else "Non-Mating"

            print(f"Contract detector result: {pred_name} (score: {score:.6f}, threshold: {self.threshold:.6f})")

            return pred_label == 1
        except Exception as e:
            print(f"Contract detector error: {e}")
            return False


# 全局检测器实例
contract_detector = None

def get_contract_detector():
    """
    获取全局contract检测器实例
    """
    global contract_detector
    if contract_detector is None:
        contract_detector = ContractDetector(CONTRACT_MODEL_PATH)
    return contract_detector
