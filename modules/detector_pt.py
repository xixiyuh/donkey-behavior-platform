# modules/detector_pt.py
import time
import torch
import numpy as np
from ultralytics import YOLO
from datetime import datetime
from .mating_detector import MatingDetector

class PTDetector:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)
        
        # GPU 加速：如果有 CUDA GPU 则使用 GPU 推理
        if torch.cuda.is_available():
            self.model.to('cuda')
            print(f"[PTDetector] GPU enabled: {torch.cuda.get_device_name(0)}")
        else:
            print("[PTDetector] GPU not available, using CPU")
        
        self.mating_detector = MatingDetector()

    def infer_once(self, frame_bgr: np.ndarray):
        t0 = time.time()

        # 调用ByteTrack进行跟踪
        r = self.model.track(
            frame_bgr,
            persist=True,
            verbose=False,
            tracker="bytetrack.yaml"
        )[0]

        dt = time.time() - t0
        return r, dt

    def annotate(self, frame_bgr: np.ndarray, r, camera_id=None, pen_id=None, barn_id=None):
        detections = []

        boxes = r.boxes
        ids = None
        if boxes is not None and boxes.id is not None:
            ids = boxes.id.int().cpu().tolist()

        for i, box in enumerate(boxes):
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            bbox = box.xyxy[0].cpu().numpy().tolist()
            track_id = ids[i] if ids is not None and i < len(ids) else None

            detections.append({
                "bbox": bbox,
                "confidence": conf,
                "class": r.names[cls],
                "track_id": track_id,
                "timestamp": datetime.now()
            })

        # 调用mating_detector.detect_mating，即使参数为None，detect_mating方法会使用默认值-1
        self.mating_detector.detect_mating(frame_bgr, detections, camera_id, pen_id, barn_id)

        return r.plot(
            line_width=2,
            font_size=8,
            conf=True,
            labels=True,
            boxes=True
        )