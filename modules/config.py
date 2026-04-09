from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

# ------- 模型/输入 -------
IMG_SIZE = (640, 640)  # (w,h)
CLASSES = ("standing", "mating", "lying")
NUM_CLASSES = len(CLASSES)
CONF_THRES = 0.4
IOU_THRES = 0.45

# ------- 事件检测参数 -------
MATING_EVENT_MIN_DURATION = 6
MATING_CONF_THRES = 0.4
MATING_AVG_CONF_THRES = 0.8  # mating事件平均置信度阈值，只有超过此阈值的事件才会被记录
MATING_MAX_CONF_THRES = 0.9  # mating事件最高置信度阈值，只有超过此阈值的事件才会被记录
MATING_COOLDOWN_PERIOD = 2  # mating事件冷却期（秒），连续多帧没有检测到时才结束事件
MATING_MIN_MOVEMENT = 60  # 最小移动距离阈值（像素），只有超过此阈值的事件才会被记录
MATING_HIGH_CONF_SKIP_MOVEMENT = 0.9  # 高置信度阈值，当平均置信度高于此值时，跳过移动距离检查
# ------- 截图尺寸配置 -------
MIN_WIDTH = 80  # 截图最小宽度
MIN_HEIGHT = 80  # 截图最小高度

# ------- 日志配置 -------
LOG_DIR = str(BASE_DIR / "logs")  # 日志目录
MATING_LOG_FILE = str(BASE_DIR / "logs" / "mating_events.log")  # mating事件日志文件
STANDING_LOG_FILE = str(BASE_DIR / "logs" / "standing_events.log")  # standing事件日志文件

# ------- 对比学习模型 -------
CONTRACT_MODEL_PATH = str(BASE_DIR / "models" / "contract-best.pt")  # 对比学习模型路径
# Linux 服务器使用yolo .pt 模型
PT_MODEL_PATH = str(BASE_DIR / "models" / "0710-best-YOLO.pt")


# ------- 本地流水线 / WS -------
MAX_FPS = 12
FRAME_INTERVAL = 4      #每 FRAME_INTERVAL 帧进行一次检测
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
