# modules/detector_pt.py
import time
import numpy as np
from ultralytics import YOLO
from datetime import datetime
from .mating_detector import MatingDetector

class PTDetector:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)
        self.mating_detector = MatingDetector()

    def infer_once(self, frame_bgr: np.ndarray):
        t0 = time.time()
        r = self.model.predict(frame_bgr, verbose=False)[0]
        dt = time.time() - t0
        return r, dt

    def annotate(self, frame_bgr: np.ndarray, r, camera_id=None, pen_id=None, barn_id=None):
        # 转换检测结果为字典格式
        detections = []
        for box in r.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            bbox = box.xyxy[0].cpu().numpy().tolist()
            detections.append({
                'bbox': bbox,
                'confidence': conf,
                'class': r.names[cls],
                'timestamp': datetime.now()
            })
        
        # 检测和记录mating事件
        if camera_id and pen_id and barn_id:
            self.mating_detector.detect_mating(frame_bgr, detections, camera_id, pen_id, barn_id)
        
        # ultralytics 自带画框
        return r.plot()  # 返回 BGR np.ndarray
