#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精简版YOLO11检测模块 - 专用于RKNN模型
整合了所有必要的依赖，无需额外的py_utils文件夹
"""

import os
import cv2
import numpy as np
import json
from copy import copy
from rknn.api import RKNN


# ==================== 配置参数 ====================
OBJ_THRESH = 0.25
NMS_THRESH = 0.45
IMG_SIZE = (640, 640)  # (width, height)
CLASSES = ("standing", "mating", "lying")
COCO_ID_LIST = [1, 2, 3]


# ==================== RKNN模型容器 ====================
class RKNN_model_container:
    def __init__(self, model_path, target=None, device_id=None):
        rknn = RKNN()
        rknn.load_rknn(model_path)
        
        print('--> Init runtime environment')
        if target is None:
            ret = rknn.init_runtime()
        else:
            ret = rknn.init_runtime(target=target, device_id=device_id)
        if ret != 0:
            print('Init runtime environment failed')
            exit(ret)
        print('done')
        
        self.rknn = rknn

    def run(self, inputs):
        if self.rknn is None:
            print("ERROR: rknn has been released")
            return []

        if isinstance(inputs, (list, tuple)):
            pass
        else:
            inputs = [inputs]

        result = self.rknn.inference(inputs=inputs)
        return result

    def release(self):
        if self.rknn is not None:
            self.rknn.release()
            self.rknn = None


# ==================== Letter Box相关类 ====================
class Letter_Box_Info:
    def __init__(self, shape, new_shape, w_ratio, h_ratio, dw, dh, pad_color):
        self.origin_shape = shape
        self.new_shape = new_shape
        self.w_ratio = w_ratio
        self.h_ratio = h_ratio
        self.dw = dw 
        self.dh = dh
        self.pad_color = pad_color


class COCO_test_helper:
    def __init__(self, enable_letter_box=False):
        self.record_list = []
        self.enable_ltter_box = enable_letter_box
        if self.enable_ltter_box:
            self.letter_box_info_list = []
        else:
            self.letter_box_info_list = None

    def letter_box(self, im, new_shape, pad_color=(0, 0, 0), info_need=False):
        # Resize and pad image while meeting stride-multiple constraints
        shape = im.shape[:2]  # current shape [height, width]
        if isinstance(new_shape, int):
            new_shape = (new_shape, new_shape)

        # Scale ratio
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])

        # Compute padding
        ratio = r  # width, height ratios
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding

        dw /= 2  # divide padding into 2 sides
        dh /= 2

        if shape[::-1] != new_unpad:  # resize
            im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=pad_color)  # add border
        
        if self.enable_ltter_box:
            self.letter_box_info_list.append(Letter_Box_Info(shape, new_shape, ratio, ratio, dw, dh, pad_color))
        if info_need:
            return im, ratio, (dw, dh)
        else:
            return im

    def get_real_box(self, box, in_format='xyxy'):
        bbox = copy(box)
        if self.enable_ltter_box:
            # unletter_box result
            if in_format == 'xyxy':
                bbox[:, 0] -= self.letter_box_info_list[-1].dw
                bbox[:, 0] /= self.letter_box_info_list[-1].w_ratio
                bbox[:, 0] = np.clip(bbox[:, 0], 0, self.letter_box_info_list[-1].origin_shape[1])

                bbox[:, 1] -= self.letter_box_info_list[-1].dh
                bbox[:, 1] /= self.letter_box_info_list[-1].h_ratio
                bbox[:, 1] = np.clip(bbox[:, 1], 0, self.letter_box_info_list[-1].origin_shape[0])

                bbox[:, 2] -= self.letter_box_info_list[-1].dw
                bbox[:, 2] /= self.letter_box_info_list[-1].w_ratio
                bbox[:, 2] = np.clip(bbox[:, 2], 0, self.letter_box_info_list[-1].origin_shape[1])

                bbox[:, 3] -= self.letter_box_info_list[-1].dh
                bbox[:, 3] /= self.letter_box_info_list[-1].h_ratio
                bbox[:, 3] = np.clip(bbox[:, 3], 0, self.letter_box_info_list[-1].origin_shape[0])
        return bbox


# ==================== YOLO11后处理函数 ====================
def filter_boxes(boxes, box_confidences, box_class_probs):
    """Filter boxes with object threshold."""
    box_confidences = box_confidences.reshape(-1)
    candidate, class_num = box_class_probs.shape

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

        w1 = np.maximum(0.0, xx2 - xx1 + 0.00001)
        h1 = np.maximum(0.0, yy2 - yy1 + 0.00001)
        inter = w1 * h1

        ovr = inter / (areas[i] + areas[order[1:]] - inter)
        inds = np.where(ovr <= NMS_THRESH)[0]
        order = order[inds + 1]
    keep = np.array(keep)
    return keep


def dfl(position):
    # Distribution Focal Loss (DFL)
    import torch
    x = torch.tensor(position)
    n, c, h, w = x.shape
    p_num = 4
    mc = c // p_num
    y = x.reshape(n, p_num, mc, h, w)
    y = y.softmax(2)
    acc_metrix = torch.tensor(range(mc)).float().reshape(1, 1, mc, 1, 1)
    y = (y * acc_metrix).sum(2)
    return y.numpy()


def box_process(position):
    grid_h, grid_w = position.shape[2:4]
    col, row = np.meshgrid(np.arange(0, grid_w), np.arange(0, grid_h))
    col = col.reshape(1, 1, grid_h, grid_w)
    row = row.reshape(1, 1, grid_h, grid_w)
    grid = np.concatenate((col, row), axis=1)
    stride = np.array([IMG_SIZE[1]//grid_h, IMG_SIZE[0]//grid_w]).reshape(1, 2, 1, 1)

    position = dfl(position)
    box_xy = grid + 0.5 - position[:, 0:2, :, :]
    box_xy2 = grid + 0.5 + position[:, 2:4, :, :]
    xyxy = np.concatenate((box_xy * stride, box_xy2 * stride), axis=1)

    return xyxy


def post_process(input_data):
    boxes, scores, classes_conf = [], [], []
    defualt_branch = 3
    pair_per_branch = len(input_data) // defualt_branch
    
    # Python 忽略 score_sum 输出
    for i in range(defualt_branch):
        boxes.append(box_process(input_data[pair_per_branch * i]))
        classes_conf.append(input_data[pair_per_branch * i + 1])
        scores.append(np.ones_like(input_data[pair_per_branch * i + 1][:, :1, :, :], dtype=np.float32))

    def sp_flatten(_in):
        ch = _in.shape[1]
        _in = _in.transpose(0, 2, 3, 1)
        return _in.reshape(-1, ch)

    boxes = [sp_flatten(_v) for _v in boxes]
    classes_conf = [sp_flatten(_v) for _v in classes_conf]
    scores = [sp_flatten(_v) for _v in scores]

    boxes = np.concatenate(boxes)
    classes_conf = np.concatenate(classes_conf)
    scores = np.concatenate(scores)

    # filter according to threshold
    boxes, classes, scores = filter_boxes(boxes, scores, classes_conf)

    # nms
    nboxes, nclasses, nscores = [], [], []
    for c in set(classes):
        inds = np.where(classes == c)
        b = boxes[inds]
        c = classes[inds]
        s = scores[inds]
        keep = nms_boxes(b, s)

        if len(keep) != 0:
            nboxes.append(b[keep])
            nclasses.append(c[keep])
            nscores.append(s[keep])

    if not nclasses and not nscores:
        return None, None, None

    boxes = np.concatenate(nboxes)
    classes = np.concatenate(nclasses)
    scores = np.concatenate(nscores)

    return boxes, classes, scores


def draw_detections(image, boxes, scores, classes):
    """在图像上绘制检测结果"""
    for box, score, cl in zip(boxes, scores, classes):
        top, left, right, bottom = [int(_b) for _b in box]
        print(f"{CLASSES[cl]} @ ({top} {left} {right} {bottom}) {score:.3f}")
        cv2.rectangle(image, (top, left), (right, bottom), (255, 0, 0), 2)
        cv2.putText(image, f'{CLASSES[cl]} {score:.2f}',
                    (top, left - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)


# ==================== YOLO11检测器主类 ====================
class YOLO11Detector:
    def __init__(self, model_path, target='rk3588', device_id=None):
        """
        初始化YOLO11检测器
        Args:
            model_path: RKNN模型路径
            target: 目标平台 (默认: 'rk3588')
            device_id: 设备ID (默认: None)
        """
        self.model = RKNN_model_container(model_path, target, device_id)
        self.co_helper = COCO_test_helper(enable_letter_box=True)
        
    def preprocess(self, img_src):
        """图像预处理"""
        # letterbox缩放
        pad_color = (0, 0, 0)
        img = self.co_helper.letter_box(
            im=img_src.copy(), 
            new_shape=(IMG_SIZE[1], IMG_SIZE[0]), 
            pad_color=pad_color
        )
        # BGR转RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return img
        
    def detect(self, img_src):
        """
        检测函数
        Args:
            img_src: 输入图像 (BGR格式)
        Returns:
            boxes: 检测框 (原图坐标系)
            classes: 类别ID
            scores: 置信度
        """
        # 预处理
        img = self.preprocess(img_src)
        
        # 推理
        outputs = self.model.run([img])
        
        # 后处理
        boxes, classes, scores = post_process(outputs)
        
        if boxes is not None:
            # 将检测框坐标转换回原图坐标系
            boxes = self.co_helper.get_real_box(boxes)
            
        return boxes, classes, scores
    
    def detect_image(self, image_path, save_path=None, show=False):
        """
        检测单张图像
        Args:
            image_path: 图像路径
            save_path: 保存路径 (可选)
            show: 是否显示结果 (默认: False)
        Returns:
            boxes, classes, scores: 检测结果
        """
        # 读取图像
        img_src = cv2.imread(image_path)
        if img_src is None:
            print(f"Error: Cannot read image {image_path}")
            return None, None, None
            
        # 检测
        boxes, classes, scores = self.detect(img_src)
        
        # 绘制结果
        if boxes is not None and (save_path or show):
            img_result = img_src.copy()
            draw_detections(img_result, boxes, scores, classes)
            
            if save_path:
                cv2.imwrite(save_path, img_result)
                print(f"Detection result saved to {save_path}")
                
            if show:
                cv2.imshow("YOLO11 Detection Result", img_result)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
        
        return boxes, classes, scores
    
    def detect_folder(self, folder_path, output_folder=None):
        """
        批量检测文件夹中的图像
        Args:
            folder_path: 输入文件夹路径
            output_folder: 输出文件夹路径 (可选)
        """
        # 支持的图像格式
        img_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        
        # 获取所有图像文件
        img_files = []
        for file in os.listdir(folder_path):
            if any(file.lower().endswith(ext) for ext in img_extensions):
                img_files.append(file)
        
        if not img_files:
            print("No image files found in the folder.")
            return
            
        # 创建输出文件夹
        if output_folder and not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        print(f"Processing {len(img_files)} images...")
        
        for i, img_file in enumerate(img_files):
            print(f'Processing {i+1}/{len(img_files)}: {img_file}', end='\r')
            
            img_path = os.path.join(folder_path, img_file)
            save_path = None
            if output_folder:
                save_path = os.path.join(output_folder, img_file)
            
            self.detect_image(img_path, save_path)
            
        print(f"\nCompleted processing {len(img_files)} images!")
    
    def release(self):
        """释放模型资源"""
        if self.model:
            self.model.release()


# ==================== 命令行接口 ====================
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='YOLO11 RKNN Detection')
    parser.add_argument('--model_path', type=str, required=True, help='RKNN model path')
    parser.add_argument('--target', type=str, default='rk3588', help='Target RKNPU platform')
    parser.add_argument('--device_id', type=str, default=None, help='Device ID')
    
    parser.add_argument('--image', type=str, help='Single image path')
    parser.add_argument('--folder', type=str, help='Image folder path')
    parser.add_argument('--output', type=str, help='Output path/folder')
    
    parser.add_argument('--show', action='store_true', help='Show detection result')
    
    args = parser.parse_args()
    
    # 初始化检测器
    detector = YOLO11Detector(args.model_path, args.target, args.device_id)
    
    try:
        if args.image:
            # 检测单张图像
            detector.detect_image(args.image, args.output, args.show)
        elif args.folder:
            # 批量检测
            detector.detect_folder(args.folder, args.output)
        else:
            print("Please specify --image or --folder")
            
    finally:
        # 释放资源
        detector.release()


# ==================== 使用示例 ====================
"""
使用示例:

1. 检测单张图像:
python yolo11_detector.py --model_path model.rknn --image test.jpg --output result.jpg --show

2. 批量检测:
python yolo11_detector.py --model_path model.rknn --folder ./images --output ./results

3. 在代码中使用:
detector = YOLO11Detector('model.rknn')
boxes, classes, scores = detector.detect(image)
detector.release()
"""
