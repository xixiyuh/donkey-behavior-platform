# modules/mating_detector.py
import os
import time
import cv2
import numpy as np
from datetime import datetime
from backend.database import get_db_connection
from .config import MATING_EVENT_MIN_DURATION, MATING_CONF_THRES

class MatingDetector:
    def __init__(self):
        self.current_mating_events = {}
        self.screenshots_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'mating_screenshots')
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    def detect_mating(self, frame, detections, camera_id, pen_id, barn_id):
        """
        检测standing事件并记录
        
        Args:
            frame: 当前帧
            detections: 检测结果
            camera_id: 摄像头ID
            pen_id: 栏ID
            barn_id: 舍ID
        """
        # 检查超时事件
        self.check_timeout_events()
        
        # 打印检测结果
        print(f"[DETECTION] Received {len(detections)} objects for camera {camera_id}, pen {pen_id}, barn {barn_id}")
        for d in detections:
            print(f"[DETECTION]   - {d['class']} (conf: {d['confidence']:.2f}, track_id: {d.get('track_id')})")
        
        # 过滤出standing类型的检测结果
        standing_detections = [d for d in detections if d['class'] == 'standing' and d['confidence'] > MATING_CONF_THRES]
        print(f"[DETECTION] Filtered standing detections: {len(standing_detections)} (confidence threshold: {MATING_CONF_THRES})")
        
        # 检查是否有standing事件
        if standing_detections:
            # 为每个standing检测结果创建或更新事件
            for detection in standing_detections:
                # 使用track_id来区分不同的standing事件
                track_id = detection.get('track_id')
                print(f"Processing detection with track_id: {track_id}")
                if track_id is not None:
                    # 构建事件键，包含track_id以区分不同的standing事件
                    # 优化事件键，使用简洁的标识符
                    camera_key = camera_id.split('/')[-1].split('?')[0] if camera_id else 'unknown'
                    event_key = f"{camera_key}_{pen_id}_{barn_id}_{track_id}"
                    print(f"Event key: {event_key}")
                    
                    if event_key not in self.current_mating_events:
                        # 开始新的standing事件
                        print(f"Starting new event: {event_key}")
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
                        # 更新现有的standing事件
                        event = self.current_mating_events[event_key]
                        event['detections'].append(detection)
                        print(f"Updating event: {event_key}, detection count: {len(event['detections'])}")
                        
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
            # 没有standing检测结果，检查是否有正在进行的standing事件需要结束
            # 构建基础事件键前缀
            base_event_key = f"{camera_id}_{pen_id}_{barn_id}_"
            # 找出所有以该前缀开头的事件键
            event_keys_to_remove = []
            for event_key in self.current_mating_events:
                if event_key.startswith(base_event_key):
                    event_keys_to_remove.append(event_key)
            
            # 结束这些事件
            print(f"Ending events: {event_keys_to_remove}")
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
        print(f"Event duration: {duration}s")
        
        # 检查事件持续时间是否达到阈值
        if duration < MATING_EVENT_MIN_DURATION:
            print(f"Standing event skipped (duration too short): camera={event['camera_id']}, pen={event['pen_id']}, barn={event['barn_id']}, duration={duration}s")
            return
        
        # 计算平均置信度和最大置信度
        confidences = [d['confidence'] for d in event['detections']]
        avg_confidence = np.mean(confidences) if confidences else 0
        max_confidence = max(confidences) if confidences else 0
        
        # 选择置信度最高的截图
        screenshot = None
        if event['screenshots']:
            # 找出最大置信度对应的截图
            max_conf_index = confidences.index(max_confidence)
            # 确保索引在有效范围内
            if max_conf_index < len(event['screenshots']):
                screenshot = event['screenshots'][max_conf_index]
            else:
                # 如果索引超出范围，使用最后一张截图
                screenshot = event['screenshots'][-1]
        
        # 记录到数据库
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO mating_events (camera_id, pen_id, barn_id, start_time, end_time, duration, 
                                       avg_confidence, max_confidence, screenshot)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (event['camera_id'], event['pen_id'], event['barn_id'], 
                  event['start_time'], end_time, duration, avg_confidence, max_confidence, 
                  screenshot))
            conn.commit()
            conn.close()
            print(f"Standing event recorded: camera={event['camera_id']}, pen={event['pen_id']}, barn={event['barn_id']}, duration={duration}s, avg_conf={avg_confidence:.2f}")
        except Exception as e:
            print(f"Error recording event: {e}")
    
    def check_timeout_events(self, timeout=30):
        """
        检查超时的mating事件并结束它们
        
        Args:
            timeout: 超时时间（秒）
        """
        current_time = datetime.now()
        keys_to_remove = []
        
        for event_key, event in self.current_mating_events.items():
            # 计算事件持续时间
            duration = (current_time - event['start_time']).total_seconds()
            # 如果事件持续时间超过超时时间，结束事件
            if duration > timeout:
                keys_to_remove.append(event_key)
        
        for key in keys_to_remove:
            self.end_mating_event(key)