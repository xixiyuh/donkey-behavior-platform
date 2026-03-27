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

# ------- 事件检测参数 -------
MATING_EVENT_MIN_DURATION = 6  # 最小mating事件持续时间（秒）

# ------- 摄像头FLV地址配置 -------
# 格式：{barn_id: {pen_id: [camera1_url, camera2_url, camera3_url]}}
CAMERA_FLV_URLS = {
    1: {
        1: [
            "https://rtmp16open.ys7.com:9188/v3/openlive/FR3098735_1_2.flv?expire=1799307668&id=930848885333229568&t=3d7f5c7af02f666391f092204cae900f60e075481b289e74400314063d7f0085&ev=101&supportH265=1",
            "https://rtmp16open.ys7.com:9188/v3/openlive/FR3098735_1_3.flv?expire=1799307668&id=930848885333229568&t=3d7f5c7af02f666391f092204cae900f60e075481b289e74400314063d7f0085&ev=101&supportH265=1",
            "https://rtmp16open.ys7.com:9188/v3/openlive/FR3098735_1_4.flv?expire=1799307668&id=930848885333229568&t=3d7f5c7af02f666391f092204cae900f60e075481b289e74400314063d7f0085&ev=101&supportH265=1"
        ],
        2: [
            "https://rtmp16open.ys7.com:9188/v3/openlive/FR3098735_2_2.flv?expire=1799307668&id=930848885333229568&t=3d7f5c7af02f666391f092204cae900f60e075481b289e74400314063d7f0085&ev=101&supportH265=1",
            "https://rtmp16open.ys7.com:9188/v3/openlive/FR3098735_2_3.flv?expire=1799307668&id=930848885333229568&t=3d7f5c7af02f666391f092204cae900f60e075481b289e74400314063d7f0085&ev=101&supportH265=1",
            "https://rtmp16open.ys7.com:9188/v3/openlive/FR3098735_2_4.flv?expire=1799307668&id=930848885333229568&t=3d7f5c7af02f666391f092204cae900f60e075481b289e74400314063d7f0085&ev=101&supportH265=1"
        ],
        # 可以继续添加更多栏的摄像头地址
    },
    2: {
        1: [
            "https://rtmp16open.ys7.com:9188/v3/openlive/FR3098735_16_2.flv?expire=1799376370&id=931137041373081600&t=4d1ff7477c74c407a64011907deb7cb38b612dfe2ec0a2fac020ae851c409a29&ev=101&supportH265=1",
            "https://rtmp16open.ys7.com:9188/v3/openlive/FR3098735_16_3.flv?expire=1799376370&id=931137041373081600&t=4d1ff7477c74c407a64011907deb7cb38b612dfe2ec0a2fac020ae851c409a29&ev=101&supportH265=1",
            "https://rtmp16open.ys7.com:9188/v3/openlive/FR3098735_16_4.flv?expire=1799376370&id=931137041373081600&t=4d1ff7477c74c407a64011907deb7cb38b612dfe2ec0a2fac020ae851c409a29&ev=101&supportH265=1"
        ],
        # 可以继续添加更多栏的摄像头地址
    }
    # 可以继续添加更多舍的摄像头地址
}
