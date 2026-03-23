# modules/overlays.py
import cv2
import modules.config as C

_COLOR_MAP = {
    0: C.COLOR_STANDING,  # standing
    1: C.COLOR_MATING,    # mating
    2: C.COLOR_LYING,     # lying
}

def draw_detections(img, dets):
    """
    dets: ndarray [N,6] = [x1,y1,x2,y2,score,class_id]
    """
    if dets is None or len(dets) == 0:
        return img
    h, w = img.shape[:2]

    for d in dets:
        x1, y1, x2, y2, sc, cid = d
        x1 = int(max(0, min(x1, w - 1)))
        y1 = int(max(0, min(y1, h - 1)))
        x2 = int(max(0, min(x2, w - 1)))
        y2 = int(max(0, min(y2, h - 1)))

        cid = int(cid)
        color = _COLOR_MAP.get(cid, (0, 255, 255))
        name = C.CLASSES[cid] if 0 <= cid < C.NUM_CLASSES else str(cid)

        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        label = f"{name}:{sc:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(img, (x1, max(0, y1 - th - 6)), (x1 + tw + 2, y1), color, -1)
        cv2.putText(img, label, (x1 + 1, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    return img

def put_fps(img, fps: float):
    fps_text = f"FPS: {fps:.1f}"
    cv2.putText(img, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (50, 220, 50), 2)
    return img

