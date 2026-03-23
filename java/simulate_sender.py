# pressure_test.py
import time
import random
import threading
import requests
from datetime import datetime, timezone

BACKEND_URL = "http://127.0.0.1:8081/api/v1/ingest/mating-events"

DEVICE_ID = "rk3588-test"   # 确保数据库里有规则（或者打开 auto-create）
VIDEO_ID = "cam1"

IMG_W, IMG_H = 1920, 1080

YOLO_VERSION = "sim-yolo"
CONTRASTIVE_VERSION = "sim-contrastive"
PIPELINE_VERSION = "sim-v1"

SESSION = requests.Session()


def build_one_event(frame_index: int, cx: int, cy: int):
    """构造一条符合规则的事件：
    - bbox 在上半区 (cy < IMG_H * 0.5)
    - 面积 >= 5000
    - 宽高比在 [0.8, 3.0] 内
    """
    # 固定一个 200x200 的框，面积=40000 > 5000，比值=1.0
    w = 200
    h = 200
    x1 = cx - w // 2
    y1 = cy - h // 2
    x2 = x1 + w
    y2 = y1 + h

    # 边界裁剪一下
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(IMG_W - 1, x2)
    y2 = min(IMG_H - 1, y2)

    yolo_conf = round(random.uniform(0.85, 0.99), 3)
    contrastive_prob = round(random.uniform(0.8, 0.99), 3)

    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    payload = {
        "deviceId": DEVICE_ID,
        "videoId": VIDEO_ID,
        "frameIndex": frame_index,
        "ts": ts,
        "yoloConf": yolo_conf,
        "contrastiveProb": contrastive_prob,
        "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
        "center": {"x": cx, "y": cy},
        "imgSize": {"w": IMG_W, "h": IMG_H},
        "model": {
            "yolo": YOLO_VERSION,
            "contrastive": CONTRASTIVE_VERSION,
            "version": PIPELINE_VERSION,
        },
        # 压测时可以先不带截图 URL
        "screenshotUrl": None,
    }
    return payload


def send_event(payload):
    try:
        resp = SESSION.post(BACKEND_URL, json=payload, timeout=2)
        return resp.status_code, resp.text
    except Exception as e:
        return None, str(e)


def episode(start_frame: int, base_cx: int, base_cy: int, count: int, interval_sec: float):
    """一次“行为 episode”：
    - 在同一位置附近，短时间内连发 count 条
    - 用于满足 10s/60s 的窗口计数 & 位置方差约束
    """
    for i in range(count):
        # center 附近轻微抖动，模拟动物活动，位置方差不会太大
        cx = base_cx + random.randint(-20, 20)
        cy = base_cy + random.randint(-20, 20)

        payload = build_one_event(start_frame + i, cx, cy)
        status, text = send_event(payload)
        print(f"[episode] frame={start_frame + i}, status={status}, resp={text[:100]}")
        time.sleep(interval_sec)


def worker_thread(thread_id: int, episodes: int):
    """压测线程：每个线程跑多个 episode"""
    frame_idx = thread_id * 100000  # 避免不同线程 frameIndex 冲突
    for ep in range(episodes):
        # 每个 episode 换一个上半区位置（避免时空去重过于激进）
        base_cx = random.randint(300, IMG_W - 300)
        base_cy = random.randint(100, IMG_H // 2 - 100)  # 上半区

        # 每个 episode 在 5 秒左右发 10 条
        episode(start_frame=frame_idx,
                base_cx=base_cx,
                base_cy=base_cy,
                count=10,
                interval_sec=0.5)
        frame_idx += 10

        # 两个 episode 之间隔 25 秒，超过 dedup_time_sec=20，保证能再产生有效事件
        print(f"[thread {thread_id}] episode {ep} done, sleep 25s...")
        time.sleep(25)


def main():
    threads = []
    thread_num = 2      # 可调：线程数
    episodes_per_thread = 3  # 每个线程跑多少轮 episode

    for t_id in range(thread_num):
        t = threading.Thread(target=worker_thread, args=(t_id, episodes_per_thread), daemon=True)
        t.start()
        threads.append(t)

    # 等所有线程结束
    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
