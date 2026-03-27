# modules/mating_detector.py
import os
import time
import cv2
import numpy as np
from datetime import datetime
from backend.database import get_db_connection
from .config import MATING_EVENT_MIN_DURATION

class MatingDetector:
    def __init__(self):
        self.current_mating_events = {}
        self.screenshots_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'mating_screenshots')
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    def detect_mating(self, frame, detections, camera_id, pen_id, barn_id):
        """
        检测mating事件并记录
        
        Args:
            frame: 当前帧
            detections: 检测结果
            camera_id: 摄像头ID
            pen_id: 栏ID
            barn_id: 舍ID
        """
        # 过滤出standing类型的检测结果
        mating_detections = [d for d in detections if d['class'] == 'standing' and d['confidence'] > 0.5]
        
        # 检查是否有mating事件
        if mating_detections:
            # 为每个mating检测结果创建或更新事件
            for detection in mating_detections:
                # 使用track_id来区分不同的mating事件
                track_id = detection.get('track_id')
                if track_id is not None:
                    # 构建事件键，包含track_id以区分不同的mating事件
                    event_key = f"{camera_id}_{pen_id}_{barn_id}_{track_id}"
                    
                    if event_key not in self.current_mating_events:
                        # 开始新的mating事件
                        self.current_mating_events[event_key] = {
                            'start_time': datetime.now(),
                            'detections': [detection],
                            'screenshots': [],
                            'camera_id': camera_id,
                            'pen_id': pen_id,
                            'barn_id': barn_id
                        }
                        
                        # 保存第一张截图
                        self.save_screenshot(frame, detection, event_key, 0)
                    else:
                        # 更新现有的mating事件
                        event = self.current_mating_events[event_key]
                        event['detections'].append(detection)
                        
                        # 保存置信度更高的截图（最多保存3张）
                        if len(event['screenshots']) < 3:
                            self.save_screenshot(frame, detection, event_key, len(event['screenshots']))
                        else:
                            # 检查是否有比现有截图置信度更高的
                            current_confidences = [d['confidence'] for d in event['detections'][:3]]
                            if current_confidences:
                                current_min_conf = min(current_confidences)
                                if detection['confidence'] > current_min_conf:
                                    # 替换置信度最低的截图
                                    min_idx = np.argmin(current_confidences)
                                    self.save_screenshot(frame, detection, event_key, min_idx)
        else:
            # 没有mating检测结果，检查是否有正在进行的mating事件需要结束
            # 构建基础事件键前缀
            base_event_key = f"{camera_id}_{pen_id}_{barn_id}_"
            # 找出所有以该前缀开头的事件键
            event_keys_to_remove = []
            for event_key in self.current_mating_events:
                if event_key.startswith(base_event_key):
                    event_keys_to_remove.append(event_key)
            
            # 结束这些事件
            for event_key in event_keys_to_remove:
                self.end_mating_event(event_key)
    
    def save_screenshot(self, frame, detection, event_key, index):
        """
        保存mating矩形区域的截图
        
        Args:
            frame: 当前帧
            detection: mating检测结果
            event_key: 事件键
            index: 截图索引
        """
        x1, y1, x2, y2 = map(int, detection['bbox'])
        # 确保坐标在有效范围内
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(frame.shape[1], x2)
        y2 = min(frame.shape[0], y2)
        
        # 裁剪mating矩形区域
        mating_roi = frame[y1:y2, x1:x2]
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{event_key}_{timestamp}_{index}.jpg"
        filepath = os.path.join(self.screenshots_dir, filename)
        
        # 保存截图
        cv2.imwrite(filepath, mating_roi)
        
        # 生成相对于静态文件目录的路径，用于前端访问
        relative_path = f"/static/mating_screenshots/{filename}"
        
        # 更新事件的截图列表
        event = self.current_mating_events[event_key]
        if index < len(event['screenshots']):
            event['screenshots'][index] = relative_path
        else:
            event['screenshots'].append(relative_path)
    
    def end_mating_event(self, event_key):
        """
        结束mating事件并记录到数据库
        
        Args:
            event_key: 事件键
        """
        event = self.current_mating_events.pop(event_key)
        
        # 计算事件持续时间（秒）
        end_time = datetime.now()
        duration = int((end_time - event['start_time']).total_seconds())
        
        # 检查事件持续时间是否达到阈值
        if duration < MATING_EVENT_MIN_DURATION:
            print(f"Mating event skipped (duration too short): camera={event['camera_id']}, pen={event['pen_id']}, barn={event['barn_id']}, duration={duration}s")
            return
        
        # 计算平均置信度和最大置信度
        confidences = [d['confidence'] for d in event['detections']]
        avg_confidence = np.mean(confidences) if confidences else 0
        max_confidence = max(confidences) if confidences else 0
        
        # 确保有3张截图（如果不足，重复最后一张）
        screenshots = event['screenshots']
        while len(screenshots) < 3:
            if screenshots:
                screenshots.append(screenshots[-1])
            else:
                screenshots.append(None)
        
        # 记录到数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO mating_events (camera_id, pen_id, barn_id, start_time, end_time, duration, 
                                   avg_confidence, max_confidence, screenshot1, screenshot2, screenshot3)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (event['camera_id'], event['pen_id'], event['barn_id'], 
              event['start_time'], end_time, duration, avg_confidence, max_confidence, 
              screenshots[0], screenshots[1], screenshots[2]))
        conn.commit()
        conn.close()
        
        print(f"Mating event recorded: camera={event['camera_id']}, pen={event['pen_id']}, barn={event['barn_id']}, duration={duration}s, avg_conf={avg_confidence:.2f}")
    
    def check_timeout_events(self, timeout=30):
        """
        检查超时的mating事件并结束它们
        
        Args:
            timeout: 超时时间（秒）
        """
        current_time = datetime.now()
        keys_to_remove = []
        
        for event_key, event in self.current_mating_events.items():
            last_detection_time = event['detections'][-1]['timestamp'] if event['detections'] else event['start_time']
            if (current_time - last_detection_time).total_seconds() > timeout:
                keys_to_remove.append(event_key)
        
        for key in keys_to_remove:
            self.end_mating_event(key)