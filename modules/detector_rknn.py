# modules/detector_rknn.py
import time
from typing import Tuple
import numpy as np
import cv2
from rknnlite.api import RKNNLite

import modules.config as C
from .postprocess import decode_yolo_rknn, letter_box, LetterBoxInfo
from .overlays import draw_detections


class RKNNDetector:
    """RKNN Lite2 YOLO 检测器（后处理=detect.py 逻辑，NumPy DFL，无 torch 依赖）"""

    def __init__(self):
        self.rknn = RKNNLite(verbose=False)
        print(f"Loading YOLO RKNN model: {C.YOLO_MODEL_PATH}")
        ret = self.rknn.load_rknn(C.YOLO_MODEL_PATH)
        if ret != 0:
            raise RuntimeError(f"Failed to load YOLO RKNN model: {ret}")
        ret = self.rknn.init_runtime(core_mask=C.RKNN_CORE_MASK)
        if ret != 0:
            raise RuntimeError(f"Failed to init YOLO runtime: {ret}")
        print("YOLO RKNN model loaded successfully")

    def preprocess(self, frame: np.ndarray) -> Tuple[np.ndarray, LetterBoxInfo]:
        """
        letterbox + BGR->RGB。
        返回 img: uint8, NHWC, contiguous（与 detect.py 风格一致，满足 RKNNLite 输入要求）
        注意：letter_box 的 new_shape 传入 (h, w)
        """
        img_resized, info = letter_box(frame.copy(), (C.IMG_SIZE[1], C.IMG_SIZE[0]), pad_color=(0, 0, 0))
        img = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        if img.dtype != np.uint8:
            img = img.astype(np.uint8)
        img = np.ascontiguousarray(img)  # [H, W, C], uint8
        return img, info

    def infer_once(self, frame: np.ndarray) -> Tuple[np.ndarray, float]:
        """执行一次推理；返回 dets: ndarray[N,6] = [x1,y1,x2,y2,score,class_id], dt(秒)"""
        t0 = time.time()
        img, info = self.preprocess(frame)

        # RKNNLite 需要 4 维 NHWC：添加 batch 维 [1, H, W, C]
        inp = img[np.newaxis, ...]  # uint8, NHWC

        # 推理
        outputs = self.rknn.inference(inputs=[inp])

        # 保护与调试
        if outputs is None or len(outputs) == 0:
            raise RuntimeError(
                "RKNN inference returned None/empty. "
                "Check input dtype/layout (NHWC uint8) and IMG_SIZE."
            )
        if any(o is None for o in outputs):
            bad_idx = [i for i, o in enumerate(outputs) if o is None]
            raise RuntimeError(f"RKNN inference produced None tensors at indexes {bad_idx}")
        # 如需查看输出形状，打开下一行：
        # print("DEBUG RKNN outputs shapes:", [getattr(o, 'shape', None) for o in outputs])

        dets = decode_yolo_rknn(outputs, info)  # ndarray [N,6]
        dt = time.time() - t0
        return dets, dt

    def annotate(self, frame: np.ndarray, dets: np.ndarray) -> np.ndarray:
        """在图上画框（颜色由 overlays 映射），不改变 dets 内容"""
        return draw_detections(frame, dets)

    def release(self):
        if hasattr(self, 'rknn') and self.rknn:
            self.rknn.release()

    def __del__(self):
        self.release()

