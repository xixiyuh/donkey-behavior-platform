# modules/detector_pt.py
import time
import numpy as np
from ultralytics import YOLO

class PTDetector:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)

    def infer_once(self, frame_bgr: np.ndarray):
        t0 = time.time()
        r = self.model.predict(frame_bgr, verbose=False)[0]
        dt = time.time() - t0
        return r, dt

    def annotate(self, frame_bgr: np.ndarray, r):
        # ultralytics 自带画框
        return r.plot()  # 返回 BGR np.ndarray
