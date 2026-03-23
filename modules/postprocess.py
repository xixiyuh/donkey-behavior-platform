# modules/postprocess.py
import numpy as np
import cv2
from copy import copy
from dataclasses import dataclass
from typing import List, Tuple, Optional
import modules.config as C

# 与 detect.py 保持一致的阈值/尺寸
OBJ_THRESH = C.CONF_THRES
NMS_THRESH = C.IOU_THRES
IMG_SIZE = C.IMG_SIZE  # (w, h)


@dataclass
class LetterBoxInfo:
    origin_shape: Tuple[int, int]  # (h, w)
    new_shape: Tuple[int, int]     # (h, w)
    w_ratio: float
    h_ratio: float
    dw: float
    dh: float


def letter_box(im: np.ndarray, new_shape: Tuple[int, int], pad_color=(0, 0, 0)) -> Tuple[np.ndarray, LetterBoxInfo]:
    """与 detect.py 一致的 letterbox，返回图与信息；new_shape=(h,w)"""
    shape = im.shape[:2]  # (h, w)
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    ratio = r
    new_unpad = (int(round(shape[1] * r)), int(round(shape[0] * r)))  # (w',h')
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
    dw /= 2
    dh /= 2

    if shape[::-1] != new_unpad:
        im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=pad_color)

    info = LetterBoxInfo(
        origin_shape=(shape[0], shape[1]),
        new_shape=(new_shape[0], new_shape[1]),
        w_ratio=ratio,
        h_ratio=ratio,
        dw=dw,
        dh=dh
    )
    return im, info


def unletter_box_xyxy(bbox: np.ndarray, info: LetterBoxInfo) -> np.ndarray:
    """把 xyxy 从输入尺寸还原到原图坐标"""
    b = copy(bbox)
    # x1,y1,x2,y2
    b[:, 0] -= info.dw
    b[:, 0] /= info.w_ratio
    b[:, 0] = np.clip(b[:, 0], 0, info.origin_shape[1])

    b[:, 1] -= info.dh
    b[:, 1] /= info.h_ratio
    b[:, 1] = np.clip(b[:, 1], 0, info.origin_shape[0])

    b[:, 2] -= info.dw
    b[:, 2] /= info.w_ratio
    b[:, 2] = np.clip(b[:, 2], 0, info.origin_shape[1])

    b[:, 3] -= info.dh
    b[:, 3] /= info.h_ratio
    b[:, 3] = np.clip(b[:, 3], 0, info.origin_shape[0])
    return b


def filter_boxes(boxes, box_confidences, box_class_probs):
    """Filter boxes with object threshold."""
    box_confidences = box_confidences.reshape(-1)
    class_max_score = np.max(box_class_probs, axis=-1)
    classes = np.argmax(box_class_probs, axis=-1)
    _class_pos = np.where(class_max_score * box_confidences >= OBJ_THRESH)
    scores = (class_max_score * box_confidences)[_class_pos]
    boxes = boxes[_class_pos]
    classes = classes[_class_pos]
    return boxes, classes, scores


def nms_boxes(boxes, scores):
    """Suppress non-maximal boxes."""
    x = boxes[:, 0]
    y = boxes[:, 1]
    w = boxes[:, 2] - boxes[:, 0]
    h = boxes[:, 3] - boxes[:, 1]
    areas = w * h
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x[i], x[order[1:]])
        yy1 = np.maximum(y[i], y[order[1:]])
        xx2 = np.minimum(x[i] + w[i], x[order[1:]] + w[order[1:]])
        yy2 = np.minimum(y[i] + h[i], y[order[1:]] + h[order[1:]])
        w1 = np.maximum(0.0, xx2 - xx1 + 1e-5)
        h1 = np.maximum(0.0, yy2 - yy1 + 1e-5)
        inter = w1 * h1
        ovr = inter / (areas[i] + areas[order[1:]] - inter)
        inds = np.where(ovr <= NMS_THRESH)[0]
        order = order[inds + 1]
    return np.array(keep)


# ---------- 纯 NumPy 的 DFL（替代 torch） ----------
def _softmax_np(x: np.ndarray, axis: int = -1) -> np.ndarray:
    x_max = np.max(x, axis=axis, keepdims=True)
    e = np.exp(x - x_max)
    return e / (np.sum(e, axis=axis, keepdims=True) + 1e-12)


def dfl(position: np.ndarray) -> np.ndarray:
    """
    输入: position [n, c, h, w], 其中 c = 4*mc
    输出: [n, 4, h, w] —— 每个边界的期望值
    """
    n, c, h, w = position.shape
    p_num = 4
    mc = c // p_num
    y = position.reshape(n, p_num, mc, h, w)          # [n,4,mc,h,w]
    y = _softmax_np(y, axis=2)                        # 对 mc 维 softmax
    acc = np.arange(mc, dtype=np.float32).reshape(1, 1, mc, 1, 1)
    y = (y * acc).sum(axis=2)                         # [n,4,h,w]
    return y


def box_process(position: np.ndarray) -> np.ndarray:
    grid_h, grid_w = position.shape[2:4]
    col, row = np.meshgrid(np.arange(0, grid_w), np.arange(0, grid_h))
    col = col.reshape(1, 1, grid_h, grid_w)
    row = row.reshape(1, 1, grid_h, grid_w)
    grid = np.concatenate((col, row), axis=1)
    stride = np.array([IMG_SIZE[1] // grid_h, IMG_SIZE[0] // grid_w]).reshape(1, 2, 1, 1)

    position = dfl(position)
    box_xy = grid + 0.5 - position[:, 0:2, :, :]
    box_xy2 = grid + 0.5 + position[:, 2:4, :, :]
    xyxy = np.concatenate((box_xy * stride, box_xy2 * stride), axis=1)
    return xyxy


def _sp_flatten(_in: np.ndarray) -> np.ndarray:
    ch = _in.shape[1]
    _in = _in.transpose(0, 2, 3, 1)
    return _in.reshape(-1, ch)


def _ensure_outputs_list(outputs):
    if outputs is None:
        raise ValueError("post_process(): outputs is None (RKNN inference failed).")
    if not isinstance(outputs, (list, tuple)):
        raise TypeError(f"post_process(): expect list/tuple, got {type(outputs)}")
    if len(outputs) == 0:
        raise ValueError("post_process(): empty outputs.")
    if any(o is None for o in outputs):
        bad_idx = [i for i, o in enumerate(outputs) if o is None]
        raise ValueError(f"post_process(): outputs contain None at {bad_idx}")


def post_process(outputs: List[np.ndarray]) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
    _ensure_outputs_list(outputs)

    boxes, scores, classes_conf = [], [], []
    defualt_branch = 3
    pair_per_branch = len(outputs) // defualt_branch
    # 若有额外 score_sum 输出也没关系，我们本来就忽略；//3 的切分能兼容

    for i in range(defualt_branch):
        boxes.append(box_process(outputs[pair_per_branch * i]))
        classes_conf.append(outputs[pair_per_branch * i + 1])
        scores.append(np.ones_like(outputs[pair_per_branch * i + 1][:, :1, :, :], dtype=np.float32))

    boxes = np.concatenate([_sp_flatten(v) for v in boxes])
    classes_conf = np.concatenate([_sp_flatten(v) for v in classes_conf])
    scores = np.concatenate([_sp_flatten(v) for v in scores])

    boxes, classes, scores = filter_boxes(boxes, scores, classes_conf)

    nboxes, nclasses, nscores = [], [], []
    for c in set(classes):
        inds = np.where(classes == c)
        b = boxes[inds]
        s = scores[inds]
        cidx = classes[inds]
        keep = nms_boxes(b, s)
        if len(keep) != 0:
            nboxes.append(b[keep])
            nclasses.append(cidx[keep])
            nscores.append(s[keep])

    if not nclasses and not nscores:
        return None, None, None

    boxes = np.concatenate(nboxes)
    classes = np.concatenate(nclasses)
    scores = np.concatenate(nscores)
    return boxes, classes, scores


def decode_yolo_rknn(outputs: List[np.ndarray], letter_info: LetterBoxInfo) -> np.ndarray:
    """
    输入：RKNN 原始 outputs（与 detect.py 一致的多分支），letterbox 信息
    返回：ndarray [N,6]，每行为 [x1,y1,x2,y2,score,class_id]（原图坐标，class_id 为 0/1/2）
    """
    boxes, classes, scores = post_process(outputs)
    if boxes is None or len(boxes) == 0:
        return np.empty((0, 6), dtype=np.float32)

    boxes = unletter_box_xyxy(boxes, letter_info)
    class_ids = classes.astype(np.int32)  # 0/1/2，不做 1-based 偏移
    out = np.concatenate(
        [
            boxes.astype(np.float32),
            scores.reshape(-1, 1).astype(np.float32),
            class_ids.reshape(-1, 1).astype(np.float32),
        ],
        axis=1,
    )
    return out

