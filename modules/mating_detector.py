# modules/mating_detector.py
import os
import time
import cv2
import numpy as np
from datetime import datetime
from backend.database import get_db_connection
from .config import MATING_EVENT_MIN_DURATION, MATING_CONF_THRES, MATING_AVG_CONF_THRES, MATING_MAX_CONF_THRES, MIN_WIDTH, MIN_HEIGHT, MATING_COOLDOWN_PERIOD

# 尝试导入日志配置，如果不存在则使用默认值
try:
    from .config import MATING_LOG_FILE, LOG_DIR
except ImportError:
    import os
    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parents[1]
    LOG_DIR = str(BASE_DIR / "logs")
    MATING_LOG_FILE = str(BASE_DIR / "logs" / "mating_events.log")
    print(f"Warning: LOG_DIR and MATING_LOG_FILE not found in config.py, using default values: LOG_DIR={LOG_DIR}, MATING_LOG_FILE={MATING_LOG_FILE}")

class MatingDetector:
    def __init__(self):
        self.current_mating_events = {}
        self.screenshots_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'mating_screenshots')
        os.makedirs(self.screenshots_dir, exist_ok=True)
                # 初始化日志目录
        os.makedirs(LOG_DIR, exist_ok=True)
        # 确保日志文件存在
        open(MATING_LOG_FILE, 'a').close()
    
    def _log(self, message):
        """
        记录日志到文件和控制台
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        # 输出到控制台
        print(log_message)
        # 写入日志文件
        try:
            with open(MATING_LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')
        except Exception as e:
            print(f"Error writing to log file: {e}")
    
    def _cleanup_logs(self):
        """
        每天清理一次日志文件
        """
        try:
            # 检查日志文件是否存在
            if os.path.exists(MATING_LOG_FILE):
                # 获取文件创建时间
                file_stat = os.stat(MATING_LOG_FILE)
                create_time = datetime.fromtimestamp(file_stat.st_ctime)
                # 计算文件年龄（天数）
                days_old = (datetime.now() - create_time).days
                 # 如果文件超过1天，则清理
                if days_old >= 1:
                    # 直接删除并创建新的空日志文件
                    os.remove(MATING_LOG_FILE)
                    # 创建新的空日志文件
                    open(MATING_LOG_FILE, 'w').close()
                    self._log(f"Log file cleaned up (超过1天)")
        except Exception as e:
            print(f"Error cleaning up logs: {e}")
    def _cleanup_screenshots(self, screenshots):
        """
        清理删除所有截图
        """
        for screenshot in screenshots:
            # 转换相对路径为绝对路径
            screenshot_path = os.path.join(os.path.dirname(__file__), "..", screenshot.lstrip("/"))
            # 检查文件是否存在并删除
            if os.path.exists(screenshot_path):
                try:
                    os.remove(screenshot_path)
                    self._log(f"Deleted screenshot: {screenshot_path}")
                except Exception as e:
                    self._log(f"Error deleting screenshot {screenshot_path}: {e}")
                                                                                             
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
        # 检查超时事件
        self.check_timeout_events()
        
        # 打印检测结果
        print(f"[DETECTION] Received {len(detections)} objects for camera {camera_id}, pen {pen_id}, barn {barn_id}")
        for d in detections:
            print(f"[DETECTION]   - {d['class']} (conf: {d['confidence']:.2f}, track_id: {d.get('track_id')})")
        
        # 过滤出mating类型的检测结果
        mating_detections = [d for d in detections if d['class'] == 'mating' and d['confidence'] > MATING_CONF_THRES]
        print(f"[DETECTION] Filtered mating detections: {len(mating_detections)} (confidence threshold: {MATING_CONF_THRES})")
        
        # 检查是否有mating事件
        if mating_detections:
            # 为每个mating检测结果创建或更新事件
            for detection in mating_detections:
                # 使用track_id来区分不同的mating事件
                track_id = detection.get('track_id')
                print(f"Processing detection with track_id: {track_id}")
                if track_id is not None:
                    # 构建事件键，包含track_id以区分不同的mating事件
                    # 优化事件键，使用简洁的标识符
                    camera_key = camera_id.split('/')[-1].split('?')[0] if camera_id else 'unknown'
                    event_key = f"{camera_key}_{pen_id}_{barn_id}_{track_id}"
                    print(f"Event key: {event_key}")
                    
                    if event_key not in self.current_mating_events:
                        # 开始新的mating事件
                        print(f"Starting new event: {event_key}")
                        self.current_mating_events[event_key] = {
                            'start_time': datetime.now(),
                            'detections': [detection],
                            'screenshots': [],
                            'camera_id': camera_id,
                            'pen_id': pen_id,
                            'barn_id': barn_id,
                            'last_detection_time': datetime.now(),  # 记录最后检测时间
                            'max_confidence': detection['confidence']
                        }
                        
                        # 保存第一张截图
                        self.save_screenshot(frame, detection, event_key, 0)
                        
                    else:
                        # 更新现有的mating事件
                        event = self.current_mating_events[event_key]
                        event['detections'].append(detection)
                        event['last_detection_time'] = datetime.now()  # 更新最后检测时间
                        print(f"Updating event: {event_key}, detection count: {len(event['detections'])}")
                        
                        # 只保存置信度最高的截图（只保存1张）
                        if detection['confidence'] > event['max_confidence']:
                            # 更新最高置信度
                            event['max_confidence'] = detection['confidence']
                            # 保存新的截图，替换旧的
                            self.save_screenshot(frame, detection, event_key, 0)
        else:
            # 没有mating检测结果，检查是否有正在进行的mating事件需要结束
            # 构建基础事件键前缀
            base_event_key = f"{camera_id}_{pen_id}_{barn_id}_"
            # 找出所有以该前缀开头的事件键
            event_keys_to_remove = []
            current_time = datetime.now()
            for event_key in self.current_mating_events:
                if event_key.startswith(base_event_key):
                    event = self.current_mating_events[event_key]
                    # 检查最后检测时间，只有超过冷却期才结束事件
                    last_detection_time = event.get('last_detection_time', event['start_time'])
                    if (current_time - last_detection_time).total_seconds() > MATING_COOLDOWN_PERIOD:  # 冷却期
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
        
        # ，并删除旧的截图文件，并删除旧的截图文件
        event = self.current_mating_events[event_key]
        if index < len(event['screenshots']):
            # 删除旧的截图文件
            old_screenshot = event['screenshots'][index]
            if old_screenshot:
                old_screenshot_path = os.path.join(os.path.dirname(__file__), "..", old_screenshot.lstrip("/"))
                if os.path.exists(old_screenshot_path):
                    try:
                        os.remove(old_screenshot_path)
                        self._log(f"Deleted old screenshot: {old_screenshot_path}")
                    except Exception as e:
                        self._log(f"Error deleting old screenshot {old_screenshot_path}: {e}")
            # 更新截图路径
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
        self._log(f"Event duration: {duration}s")
        # 检查并清理日志文件（每周一次）
        self._cleanup_logs()
        
        # 检查事件持续时间是否达到阈值
        if duration < MATING_EVENT_MIN_DURATION:
            self._log(f"Mating event skipped (duration too short): camera={event['camera_id']}, pen={event['pen_id']}, barn={event['barn_id']}, duration={duration}s")
            # 删除所有截图
            self._cleanup_screenshots(event['screenshots'])
            return
        
        # 计算平均置信度和最大置信度
        confidences = [d['confidence'] for d in event['detections']]
        avg_confidence = np.mean(confidences) if confidences else 0
        max_confidence = max(confidences) if confidences else 0
        # 检查平均置信度是否达到阈值
        if avg_confidence < MATING_AVG_CONF_THRES:
           self._log(f"Mating event skipped (average confidence too low): camera={event['camera_id']}, pen={event['pen_id']}, barn={event['barn_id']}, avg_conf={avg_confidence:.2f}")
           # 删除所有截图
           self._cleanup_screenshots(event['screenshots'])
           return

        # 检查最高置信度是否达到阈值
        if max_confidence < MATING_MAX_CONF_THRES:
            self._log(f"Mating event skipped (max confidence too low): camera={event['camera_id']}, pen={event['pen_id']}, barn={event['barn_id']}, max_conf={max_confidence:.2f}")
            # 删除所有截图
            self._cleanup_screenshots(event['screenshots'])
            return
        
        # 选择置信度最高的截图
        screenshot = None
        if event['screenshots']:
            screenshot = event['screenshots'][0]  # 只保存了1张，直接使用

        # 检查截图尺寸
        if screenshot:
            # 转换相对路径为绝对路径
            screenshot_path = os.path.join(os.path.dirname(__file__), "..", screenshot.lstrip("/"))
            # 检查文件是否存在
            if os.path.exists(screenshot_path):
                # 读取图片并检查尺寸
                try:
                    img = cv2.imread(screenshot_path)
                    if img is not None:
                        height, width = img.shape[:2]
                        if width < MIN_WIDTH or height < MIN_HEIGHT:
                            self._log(f"Mating event skipped (screenshot size too small): camera={event['camera_id']}, pen={event['pen_id']}, barn={event['barn_id']}, size={width}x{height}")
                            # 删除所有截图
                            self._cleanup_screenshots(event['screenshots'])
                            return
                except Exception as e:
                    self._log(f"Error checking screenshot size: {e}")
                    # 删除所有截图
                    self._cleanup_screenshots(event['screenshots'])
                    return
        else:
            self._log(f"Mating event skipped (screenshot not found): camera={event['camera_id']}, pen={event['pen_id']}, barn={event['barn_id']}")
            # 删除所有截图
            self._cleanup_screenshots(event['screenshots'])
            return

        # 使用contract detector进行二次检测(暂时禁用)
        if screenshot:
            # 转换相对路径为绝对路径
            screenshot_path = os.path.join(os.path.dirname(__file__), "..", screenshot.lstrip("/"))
            contract_detector = get_contract_detector()
            is_mating = contract_detector.predict(screenshot_path)
            if not is_mating:
                self._log(f"Mating event skipped (contract detector returned non-mating): camera={event['camera_id']}, pen={event['pen_id']}, barn={event['barn_id']}")
                # 删除所有截图
                self._cleanup_screenshots(event['screenshots'])
                return
        
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
            self._log(f"Mating event recorded: camera={event['camera_id']}, pen={event['pen_id']}, barn={event['barn_id']}, duration={duration}s, avg_conf={avg_confidence:.2f}")
        except Exception as e:
            self._log(f"Error recording event: {e}")
    
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
            # 检查最后检测时间，超过冷却期也结束事件
            elif (current_time - event.get('last_detection_time', event['start_time'])).total_seconds() > MATING_COOLDOWN_PERIOD:
                keys_to_remove.append(event_key)
        
        for key in keys_to_remove:
            self.end_mating_event(key)
