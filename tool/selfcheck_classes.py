# tools/selfcheck_classes.py
# 用 detect.py 的 YOLO11Detector 做核验（不改你的后处理逻辑）

import os
import sys
import argparse
import cv2
import numpy as np

# ---- 直接复用你的 detect.py ----
# 确保 PYTHONPATH 能找到 modules/detect.py 或把 detect.py 放同层导入
# 如果 detect.py 不在同目录，请按你的项目结构调整导入路径
from detect import YOLO11Detector, CLASSES  # CLASSES = ("standing","mating","lying")

def load_images(image: str = None, folder: str = None, exts=(".jpg",".jpeg",".png",".bmp")):
    paths = []
    if image:
        paths.append(image)
    if folder:
        for n in os.listdir(folder):
            if n.lower().endswith(exts):
                paths.append(os.path.join(folder, n))
    return paths

def main():
    ap = argparse.ArgumentParser("Self-check class id/order against detect.py")
    ap.add_argument("--model_path", required=True, help="RKNN model path for detect.py")
    ap.add_argument("--target", default="rk3588", help="RKNPU target, e.g., rk3588")
    ap.add_argument("--device_id", default=None, help="RK device id")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--image", help="Single image path")
    g.add_argument("--folder", help="Folder of images")
    ap.add_argument("--max_show", type=int, default=0, help="(Optional) show first N images with drawn boxes")
    ap.add_argument("--topk", type=int, default=10, help="Print top-K detections per image")
    args = ap.parse_args()

    # 期望顺序
    expected = ("standing","mating","lying")
    if tuple(CLASSES) != expected:
        print(f"[WARN] CLASSES in detect.py = {CLASSES}, expected = {expected}")

    det = YOLO11Detector(args.model_path, target=args.target, device_id=args.device_id)

    try:
        paths = load_images(args.image, args.folder)
        if not paths:
            print("[ERR] No images found.")
            sys.exit(2)

        # 计数器
        id_hist = {0:0, 1:0, 2:0}
        name_hist = {n:0 for n in expected}
        bad_id = 0

        for idx, p in enumerate(paths, 1):
            img = cv2.imread(p)
            if img is None:
                print(f"[SKIP] cannot read: {p}")
                continue

            boxes, classes, scores = det.detect(img)  # detect.py 原生输出
            print(f"\n== [{idx}/{len(paths)}] {os.path.basename(p)} ==")
            if boxes is None or len(boxes) == 0:
                print("  no detections")
                continue

            # 打印前 topK
            K = min(args.topk, len(boxes))
            order = np.argsort(scores)[::-1][:K]
            for i in order:
                cid = int(classes[i])
                sc  = float(scores[i])
                if cid not in (0,1,2):
                    bad_id += 1
                    cid_print = f"{cid}  <-- [INVALID, should be 0/1/2]"
                else:
                    cid_print = str(cid)
                    id_hist[cid] += 1
                    name_hist[CLASSES[cid]] += 1
                x1,y1,x2,y2 = [int(v) for v in boxes[i]]
                print(f"  cid={cid_print:>6}  name={CLASSES[cid] if cid in (0,1,2) else '???':8s}  "
                      f"score={sc:.3f}  box=({x1},{y1},{x2},{y2})")

            # 可选显示（仅用于人工目测，不影响结果）
            if args.max_show > 0 and idx <= args.max_show:
                vis = img.copy()
                for i in order:
                    cid = int(classes[i])
                    sc  = float(scores[i])
                    x1,y1,x2,y2 = [int(v) for v in boxes[i]]
                    # 按 class_id 上色：0=绿, 1=红(mating), 2=蓝
                    color = (0,255,0) if cid==0 else (0,0,255) if cid==1 else (255,0,0)
                    cv2.rectangle(vis, (x1,y1), (x2,y2), color, 2)
                    cv2.putText(vis, f"{CLASSES[cid]}:{sc:.2f}", (x1, max(15,y1-6)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                cv2.imshow("selfcheck", vis)
                cv2.waitKey(0)

        # 汇总
        print("\n==== SUMMARY ====")
        print(f"invalid class_id count (not in 0/1/2): {bad_id}")
        print(f"id_hist:   {id_hist}")
        print(f"name_hist: {name_hist}")
        # 关键断言：mating 必须是 id=1
        if "mating" in CLASSES:
            mating_id = CLASSES.index("mating")
            if mating_id != 1:
                print(f"[FAIL] 'mating' index in CLASSES is {mating_id}, expected 1")
                sys.exit(3)
            else:
                print("[OK] 'mating' index == 1")
        else:
            print("[FAIL] 'mating' not found in CLASSES")
            sys.exit(4)

        if bad_id > 0:
            print("[FAIL] Found invalid class ids (not 0/1/2). Check your postprocess mapping.")
            sys.exit(5)

        print("[OK] class id/order self-check passed.")
    finally:
        det.release()
        try: cv2.destroyAllWindows()
        except: pass

if __name__ == "__main__":
    main()

