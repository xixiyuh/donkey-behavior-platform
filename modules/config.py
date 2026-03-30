from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

# ------- 模型/输入 -------
IMG_SIZE = (640, 640)  # (w,h)
CLASSES = ("standing", "mating", "lying")
NUM_CLASSES = len(CLASSES)
CONF_THRES = 0.25
IOU_THRES = 0.45

# ------- 事件检测参数 -------
MATING_EVENT_MIN_DURATION = 6
MATING_CONF_THRES = 0.4

# Linux 服务器使用 .pt 模型
PT_MODEL_PATH = str(BASE_DIR / "models" / "0710-best-YOLO.pt")

# ------- 本地流水线 / WS -------
MAX_FPS = 10
FRAME_INTERVAL = 2
JPEG_QUALITY = 60
QUEUE_MAX = 2

# ------- 输入源默认 -------
RTSP_URL = "rtsp://user:pass@ip:port/xxx"
VIDEO_PATH = str(BASE_DIR / "data" / "demo.mp4")
IMAGE_PATH = str(BASE_DIR / "data" / "111.png")

# ------- MPV Pipe -------
MPV_DIR = "/usr/bin"
MPV_EXE = "/opt/mpv/bin/mpv"

MPV_PIPE_W = 800
MPV_PIPE_H = 600
MPV_PIPE_FPS = 8

# ------- 颜色（BGR） -------
COLOR_STANDING = (0, 255, 0)
COLOR_MATING = (0, 0, 255)
COLOR_LYING = (255, 0, 0)
