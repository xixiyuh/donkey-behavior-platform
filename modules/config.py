# modules/config.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

# ------- 模型/输入 -------
IMG_SIZE = (640, 640)  # (w,h)
CLASSES = ("standing", "mating", "lying")
NUM_CLASSES = len(CLASSES)
CONF_THRES = 0.25
IOU_THRES = 0.45

# ✅ Windows 先跑 .pt
PT_MODEL_PATH = str(BASE_DIR / "models" / r"E:\donkey\萤石云\realtime-detector\models\0710-best-YOLO.pt")  # ←改成你的真实路径也行
# 例如：PT_MODEL_PATH = r"E:\donkey\萤石云\realtime-detector\models\0710-best-YOLO.pt"

# ------- 流水线 / WS -------
MAX_FPS = 20
FRAME_INTERVAL = 1
JPEG_QUALITY = 80
QUEUE_MAX = 2

# ------- 输入源默认 -------
RTSP_URL = "rtsp://user:pass@ip:port/xxx"
VIDEO_PATH = str(BASE_DIR / "data" / "demo.mp4")
IMAGE_PATH = str(BASE_DIR / "data" / "111.png")

# ------- MPV Pipe（用 mpv.exe 拉流并吐 rawvideo）-------
MPV_DIR = r"D:\mpv\mpv-x86_64-20260104-git-a3350e2"  # ←改成你 mpv.exe 所在目录
MPV_EXE = r"D:\mpv\mpv-x86_64-20260104-git-a3350e2\mpv.exe"


# mpvpipe 输出帧的固定尺寸（必须固定，才能按字节流切帧）
MPV_PIPE_W = 1280
MPV_PIPE_H = 720
MPV_PIPE_FPS = 15

# ------- 颜色（BGR） -------
COLOR_STANDING = (0, 255, 0)
COLOR_MATING = (0, 0, 255)
COLOR_LYING = (255, 0, 0)
