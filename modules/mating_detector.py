# modules/mating_detector.py
import os
import time
import cv2
import numpy as np
from datetime import datetime
from backend.database import get_db_connection

class MatingDetector:
    def __init__(self):
        self.current_mating_events = {}
        self.screenshots_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'mating_screenshots')
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
        # 过滤出mating类型的检测结果
        mating_detections = [d for d in detections if d['class'] == 'mating' and d['confidence'] > 0.5]
        
        # 检查是否有mating事件
        if mating_detections:
            # 获取置信度最高的mating检测结果
            best_mating = max(mating_detections, key=lambda x: x['confidence'])
            
            # 检查是否已经有正在进行的mating事件
            event_key = f"{camera_id}_{pen_id}_{barn_id}"
            if event_key not in self.current_mating_events:
                # 开始新的mating事件
                self.current_mating_events[event_key] = {
                    'start_time': datetime.now(),
                    'detections': [best_mating],
                    'screenshots': [],
                    'camera_id': camera_id,
                    'pen_id': pen_id,
                    'barn_id': barn_id
                }
                
                # 保存第一张截图
                self.save_screenshot(frame, best_mating, event_key, 0)
            else:
                # 更新现有的mating事件
                event = self.current_mating_events[event_key]
                event['detections'].append(best_mating)
                
                # 保存置信度更高的截图（最多保存3张）
                if len(event['screenshots']) < 3:
                    self.save_screenshot(frame, best_mating, event_key, len(event['screenshots']))
                else:
                    # 检查是否有比现有截图置信度更高的
                    current_max_conf = max([d['confidence'] for d in event['detections'][:3]])
                    if best_mating['confidence'] > current_max_conf:
                        # 替换置信度最低的截图
                        min_idx = np.argmin([d['confidence'] for d in event['detections'][:3]])
                        self.save_screenshot(frame, best_mating, event_key, min_idx)
                        event['detections'][min_idx] = best_mating
        else:
            # 没有mating检测结果，检查是否有正在进行的mating事件需要结束
            event_key = f"{camera_id}_{pen_id}_{barn_id}"
            if event_key in self.current_mating_events:
                # 结束mating事件并记录到数据库
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
        
        # 更新事件的截图列表
        event = self.current_mating_events[event_key]
        if index < len(event['screenshots']):
            event['screenshots'][index] = filepath
        else:
            event['screenshots'].append(filepath)
    
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