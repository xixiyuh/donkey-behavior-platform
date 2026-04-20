"""
源会话管理器 - 实现同源 pipeline 共享与多订阅者架构 + 后台/展示结果分离

核心理念：
- 同一视频源（kind+value）只有一个 SourceSession
- 一个 SourceSession 只有一套 reader + infer 线程
- 多个 WebSocket 只作为该 session 的订阅者，接收广播结果
- TTL 空闲释放机制：最后一个订阅者离开后，等待 TTL 再销毁

关键优化：
1. 分离"检测结果"和"展示结果"：
   - detection_result：用于后台事件过滤、截图、落库等业务逻辑
   - display_frame：仅当有WebSocket订阅者时才生成（包含绘制的框和编码）

2. 引入版本机制：
   - frame_version：每读到新帧 +1
   - result_version：每生成新检测结果 +1
   - display_version：每生成新展示帧 +1
   - 避免重复处理和重复编码

3. 避免忙轮询：
   - 使用 Event 替代 time.sleep() 轮询
   - 新帧或订阅者变化时发信号

4. 后台模式优化：
   - 只有有WebSocket订阅者时才生成展示帧和编码JPEG
   - 后台模式下只做检测和事件处理
"""

import threading
import queue
import time
import asyncio
from typing import Dict, Tuple, Optional, Any, List, Set
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict

import numpy as np
import cv2

from . import config as C
from .streams import open_source
from .detector_pt import PTDetector
from .logger import inf, dbg, wrn, err

def get_timestamp():
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")


@dataclass
class SourceKey:
    """视频源唯一标识：(kind, value, camera_id)
    
    比较逻辑：
    - 如果有 camera_id，则仅用 camera_id 来判断相等性（同一摄像头无论访问方式不同都视为同源）
    - 如果没有 camera_id，则用 (kind, value) 来判断相等性
    """
    kind: str
    value: str
    camera_id: Optional[str] = None
    pen_id: Optional[int] = None
    barn_id: Optional[int] = None
    
    def __hash__(self):
        # 如果有 camera_id，优先使用 camera_id 作为唯一标识
        if self.camera_id:
            return hash(('camera_id', self.camera_id))
        return hash((self.kind, self.value))
    
    def __eq__(self, other):
        if not isinstance(other, SourceKey):
            return False
        
        # 优先比较 camera_id（如果有的话）
        # 这确保相同摄像头无论怎样访问（前端 mpv / 后台 flv）都被认为是同一源
        if self.camera_id and other.camera_id:
            return self.camera_id == other.camera_id
        
        # 都没有 camera_id 时，才比较 kind 和 value
        if not self.camera_id and not other.camera_id:
            return self.kind == other.kind and self.value == other.value
        
        # 一个有 camera_id 一个没有，不相等
        return False
    
    def __repr__(self):
        cam_suffix = f"@{self.camera_id}" if self.camera_id else ""
        if self.camera_id:
            # 如果有 camera_id，则主要展示 camera_id
            return f"SourceKey(camera={self.camera_id})"
        return f"SourceKey({self.kind}:{self.value[:30]}...{cam_suffix})"


class SourceSession:
    """
    单个视频源的会话
    
    职责：
    - 持有 stream 和 detector
    - 运行 reader + infer 线程
    - 维护最新帧、检测结果和展示结果
    - 向多个订阅者广播结果
    - 管理订阅者增删和引用计数
    - 分离后台检测逻辑和前端展示逻辑
    
    架构：
    A. 后台检测层（永远需要）：
       - latest_frame + frame_version
       - detection_result + result_version
       - 用于事件过滤、截图、落库
    
    B. 展示层（仅当有 WebSocket 订阅者时）：
       - latest_display_frame + display_version
       - latest_jpeg_bytes（JPEG 编码，多订阅者共享）
       - 用于 WebSocket 推送
    """
    
    def __init__(self, source_key: SourceKey, stream, detector: PTDetector):
        self.source_key = source_key
        self.stream = stream
        self.detector = detector
        
        # 订阅者管理
        self.subscribers: Set[Any] = set()  # 存储 WebSocket 连接
        self.ref_count = 0
        self.subscribers_lock = threading.RLock()
        self.subscribers_changed_event = threading.Event()  # 订阅者变化信号
        
        # ===== 后台检测层（必须保留）=====
        self.latest_frame = None
        self.frame_version = 0
        self.frame_lock = threading.RLock()
        
        # 检测结果：保存推理原始结果（不含框）
        self.detection_result = None  # {"bbox": [...], "confidence": [...], ...}
        self.result_version = 0
        self.result_lock = threading.RLock()
        
        # ===== 展示层（仅在有订阅者时生成）=====
        self.latest_display_frame = None
        self.display_version = 0
        self.latest_jpeg_bytes = None
        self.display_lock = threading.RLock()
        
        # 线程控制
        self.stop_event = threading.Event()
        self.new_frame_event = threading.Event()  # 新帧信号
        self.reader_thread: Optional[threading.Thread] = None
        self.infer_thread: Optional[threading.Thread] = None
        
        # 空闲超时
        self.last_active_time = time.time()
        self.idle_timeout = 60  # 秒
        
        # 元数据和统计
        self.created_at = datetime.now()
        self.metadata = {
            'kind': source_key.kind,
            'value': source_key.value,
            'camera_id': source_key.camera_id,
            'pen_id': source_key.pen_id,
            'barn_id': source_key.barn_id,
        }
        
        # 性能统计计数器
        self.start_count = 0  # pipeline启动次数
        self.infer_count = 0  # 推理次数
        self.display_encode_count = 0  # 展示帧编码次数
        self.broadcast_count = 0  # 广播次数
        self.frame_no = 0  # 帧编号
        self.last_infer_cost_ms = 0  # 最后推理耗时
        self.infer_times = []  # 推理耗时历史（最多保留100条）
        self.reader_alive = False
        self.infer_alive = False
        
        inf(f"[SESSION] Created source_key={source_key} session_id={id(self)} stream_id={id(stream)}")
    
    def add_subscriber(self, ws) -> None:
        """添加订阅者，并发送信号"""
        with self.subscribers_lock:
            if ws not in self.subscribers:
                self.subscribers.add(ws)
                self.ref_count += 1
                self.last_active_time = time.time()
                # 订阅者变化，发送信号
                self.subscribers_changed_event.set()
                print(f"{get_timestamp()} [SourceSession] {self.source_key} add subscriber, ref_count={self.ref_count}", 
                      flush=True)
    
    def remove_subscriber(self, ws) -> int:
        """移除订阅者，返回当前 ref_count，并发送信号"""
        with self.subscribers_lock:
            if ws in self.subscribers:
                self.subscribers.discard(ws)
                self.ref_count -= 1
                self.last_active_time = time.time()
                # 订阅者变化，发送信号
                self.subscribers_changed_event.set()
                print(f"{get_timestamp()} [SourceSession] {self.source_key} remove subscriber, ref_count={self.ref_count}", 
                      flush=True)
            return self.ref_count
    
    def get_ws_subscriber_count(self) -> int:
        """获取 WebSocket 订阅者数量"""
        with self.subscribers_lock:
            return len(self.subscribers)
    
    def is_idle(self) -> bool:
        """检查是否空闲（无订阅者且超时）"""
        with self.subscribers_lock:
            if self.ref_count > 0:
                return False
        return (time.time() - self.last_active_time) > self.idle_timeout
    
    def start(self) -> None:
        """启动 reader 和 infer 线程"""
        if self.reader_thread is None:
            self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
            self.reader_thread.start()
        if self.infer_thread is None:
            self.infer_thread = threading.Thread(target=self._infer_loop, daemon=True)
            self.infer_thread.start()
        
        # 增加启动计数
        self.start_count += 1
        inf(f"[PIPELINE-START] source_key={self.source_key} start_count={self.start_count} reader_thread={self.reader_thread.name if self.reader_thread else None} infer_thread={self.infer_thread.name if self.infer_thread else None}")
    
    def stop(self) -> None:
        """停止 session"""
        inf(f"[SourceSession] {self.source_key} stopping...")
        
        try:
            # 通知线程停止
            self.stop_event.set()
            
            # 等待线程退出（短超时，因为线程是daemon）
            if self.reader_thread and self.reader_thread.is_alive():
                self.reader_thread.join(timeout=1.0)
            if self.infer_thread and self.infer_thread.is_alive():
                self.infer_thread.join(timeout=1.0)
        except Exception as e:
            err(f"[SourceSession] Error stopping threads: {e}")
        
        # 关闭流
        try:
            if hasattr(self.stream, 'release'):
                self.stream.release()
        except Exception as e:
            err(f"[SourceSession] Error releasing stream: {e}")
        
        inf(f"[SourceSession] {self.source_key} stopped")
    
    def _reader_loop(self) -> None:
        """读取线程 - 持续读取流的最新帧，避免忙轮询"""
        print(f"{get_timestamp()} [Reader] {self.source_key} started", flush=True)
        consecutive_failures = 0
        max_consecutive_failures = 10
        self.reader_alive = True
        
        try:
            while not self.stop_event.is_set():
                try:
                    ok, frame = self.stream.read()
                    
                    if ok and frame is not None:
                        # 保存最新帧，递增版本号
                        with self.frame_lock:
                            self.latest_frame = frame
                            self.frame_version += 1
                            current_version = self.frame_version
                        consecutive_failures = 0
                        # 发送新帧信号，唤醒 infer 线程
                        self.new_frame_event.set()
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= max_consecutive_failures:
                            print(f"{get_timestamp()} [Reader] {self.source_key} stream failed, stopping", 
                                  flush=True)
                            self.stop_event.set()
                            break
                        # 等待而不是忙轮询
                        self.new_frame_event.clear()
                        self.new_frame_event.wait(timeout=0.05)
                
                except Exception as e:
                    print(f"{get_timestamp()} [Reader] {self.source_key} read error: {e}", flush=True)
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        self.stop_event.set()
                        break
                    self.new_frame_event.clear()
                    self.new_frame_event.wait(timeout=0.05)
        
        except Exception as e:
            print(f"{get_timestamp()} [Reader] {self.source_key} fatal error: {e}", flush=True)
        finally:
            self.reader_alive = False
            print(f"{get_timestamp()} [Reader] {self.source_key} stopped", flush=True)
    
    def _infer_loop(self) -> None:
        """
        推理线程 - 只在frame_version变化时才推理，分离后台检测和展示逻辑
        
        关键优化：
        1. 只在 frame_version 变化时才调用推理
        2. 后台检测结果：保存到 detection_result，用于事件处理
        3. 展示结果：只在有WebSocket订阅者时生成 display_frame 和 JPEG
        4. 避免忙轮询：使用 Event 来等待新帧
        5. 推理时间间隔：使用 INFER_INTERVAL_MS 控制推理频率
        """
        inf(f"[Infer] {self.source_key} started")
        idx = 0
        last_fps = 0.0
        last_frame_version = -1  # 追踪上一次处理的frame版本
        last_infer_time = 0.0  # 上一次推理的时间（秒）
        r = None  # 最后一次推理的结果
        self.infer_alive = True
        
        try:
            while not self.stop_event.is_set():
                # 获取最新帧和版本
                with self.frame_lock:
                    frame = self.latest_frame
                    current_frame_version = self.frame_version
                
                # 如果没有新帧，等待而不是忙轮询
                if frame is None or current_frame_version == last_frame_version:
                    self.new_frame_event.clear()
                    # 等待新帧或订阅者变化
                    self.new_frame_event.wait(timeout=0.01)
                    continue
                
                # 有新帧，记录版本
                last_frame_version = current_frame_version
                
                try:
                    # ===== 后台检测逻辑（必须保留）=====
                    # 跳帧推理，且检查推理时间间隔
                    should_infer = False
                    
                    if idx % max(1, C.FRAME_INTERVAL) == 0:
                        # 检查推理时间间隔（仅当配置了最小间隔时）
                        if C.INFER_INTERVAL_MS > 0:
                            current_time = time.time()
                            time_since_last_infer = (current_time - last_infer_time) * 1000  # 转换为毫秒
                            if time_since_last_infer >= C.INFER_INTERVAL_MS:
                                should_infer = True
                                last_infer_time = current_time
                        else:
                            # 无间隔限制，直接推理
                            should_infer = True
                            last_infer_time = time.time()
                    
                    if should_infer:
                        start_time = time.time()
                        r, dt = self.detector.infer_once(frame)
                        cost_ms = (time.time() - start_time) * 1000
                        self.last_infer_cost_ms = cost_ms
                        self.infer_times.append(cost_ms)
                        if len(self.infer_times) > 100:
                            self.infer_times.pop(0)
                        
                        last_fps = 1.0 / dt if dt and dt > 0 else 0.0
                        
                        # 保存检测结果（用于后台事件处理）
                        with self.result_lock:
                            self.detection_result = r
                            self.result_version += 1
                        
                        # 增加推理计数
                        self.infer_count += 1
                        
                        # 打印推理日志（每10次打印一次以减少日志量）
                        if self.infer_count % 10 == 0:
                            ws_count = self.get_ws_subscriber_count()
                            avg_cost = sum(self.infer_times) / len(self.infer_times) if self.infer_times else 0
                            infer_freq = 1000.0 / C.INFER_INTERVAL_MS if C.INFER_INTERVAL_MS > 0 else 0
                            inf(f"[INFER] source_key={self.source_key} infer_count={self.infer_count} "
                                f"frame_no={idx} ws_subscriber_count={ws_count} "
                                f"last_cost={cost_ms:.1f}ms avg_cost={avg_cost:.1f}ms infer_freq={infer_freq:.1f}/s")
                    
                    # ===== 展示逻辑（仅当有WebSocket订阅者时才生成）=====
                    ws_subscriber_count = self.get_ws_subscriber_count()
                    
                    if ws_subscriber_count > 0:
                        # 有订阅者，生成展示帧
                        display_frame = frame.copy()
                        
                        # 绘制框（仅在展示模式）
                        if should_infer:
                            # 刚刚推理的结果，绘制最新的框
                            display_frame = self.detector.annotate(display_frame, r,
                                                                 camera_id=self.metadata.get('camera_id'),
                                                                 pen_id=self.metadata.get('pen_id'),
                                                                 barn_id=self.metadata.get('barn_id'))
                        else:
                            # 使用上一次的推理结果绘制
                            with self.result_lock:
                                if self.detection_result is not None:
                                    display_frame = self.detector.annotate(display_frame, self.detection_result,
                                                                         camera_id=self.metadata.get('camera_id'),
                                                                         pen_id=self.metadata.get('pen_id'),
                                                                         barn_id=self.metadata.get('barn_id'))
                        
                        # 绘制 FPS（仅在展示模式）
                        self._put_fps(display_frame, last_fps)
                        
                        # 保存展示结果和版本
                        with self.display_lock:
                            self.latest_display_frame = display_frame
                            self.display_version += 1
                            # 统一编码一次，多个订阅者共享（延迟编码，仅在broadcast时）
                    else:
                        # 无订阅者，不生成展示帧和JPEG（省CPU）
                        with self.display_lock:
                            self.latest_display_frame = None
                            self.latest_jpeg_bytes = None
                    
                    idx += 1
                
                except Exception as e:
                    err(f"[Infer] {self.source_key} inference error: {e}")
                    time.sleep(0.01)
        
        except Exception as e:
            err(f"[Infer] {self.source_key} fatal error: {e}")
        finally:
            self.infer_alive = False
            inf(f"[Infer] {self.source_key} stopped")
    
    def _put_fps(self, frame, fps_value):
        """绘制 FPS"""
        try:
            fps_text = f"FPS: {fps_value:.1f}"
            cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.7, (0, 255, 0), 2)
        except Exception:
            pass
    
    def get_latest_result(self):
        """获取最新的显示帧（用于WebSocket推送）"""
        with self.display_lock:
            return self.latest_display_frame.copy() if self.latest_display_frame is not None else None
    
    def get_detection_result(self):
        """获取最新的检测结果（用于后台事件处理，不含框）"""
        with self.result_lock:
            return self.detection_result
    
    def get_display_version(self) -> int:
        """获取展示版本号"""
        with self.display_lock:
            return self.display_version
    
    def encode_and_cache_jpeg(self, quality: int = 80):
        """
        生成并缓存 JPEG（仅当有展示帧时）
        这个方法统一生成一次 JPEG，多个订阅者共享
        返回：(jpeg_bytes, version)
        """
        with self.display_lock:
            if self.latest_display_frame is None:
                return None, self.display_version
            
            try:
                ok, buffer = cv2.imencode('.jpg', self.latest_display_frame, 
                                        [cv2.IMWRITE_JPEG_QUALITY, quality])
                if ok:
                    self.latest_jpeg_bytes = buffer.tobytes()
                    self.display_encode_count += 1
                    return self.latest_jpeg_bytes, self.display_version
            except Exception as e:
                err(f"[SourceSession] JPEG encode error: {e}")
        
        return None, self.display_version
    
    def get_cached_jpeg(self) -> Optional[bytes]:
        """获取已缓存的 JPEG bytes"""
        with self.display_lock:
            return self.latest_jpeg_bytes
    
    def get_stats(self) -> Dict[str, Any]:
        """获取会话统计信息，包含性能观测字段"""
        with self.subscribers_lock:
            ws_subscriber_count = len(self.subscribers)
            reader_alive = self.reader_thread is not None and self.reader_thread.is_alive()
            infer_alive = self.infer_thread is not None and self.infer_thread.is_alive()
        
        avg_infer_cost_ms = 0
        if self.infer_times:
            avg_infer_cost_ms = sum(self.infer_times) / len(self.infer_times)
        
        return {
            'source_key': str(self.source_key),
            'session_id': id(self),
            'stream_id': id(self.stream),
            # 订阅者信息
            'holder_count': self.ref_count,
            'ws_subscriber_count': ws_subscriber_count,
            # 线程状态
            'reader_alive': reader_alive,
            'infer_alive': infer_alive,
            # 版本号
            'frame_version': self.frame_version,
            'result_version': self.result_version,
            'display_version': self.display_version,
            # 性能计数器
            'infer_count': self.infer_count,
            'display_encode_count': self.display_encode_count,
            'broadcast_count': self.broadcast_count,
            'last_infer_cost_ms': round(self.last_infer_cost_ms, 2),
            'avg_infer_cost_ms': round(avg_infer_cost_ms, 2),
            # 时间戳
            'frame_no': self.frame_no,
            'created_at': self.created_at.isoformat(),
            'last_active_time': datetime.fromtimestamp(self.last_active_time).isoformat(),
            'is_idle': self.is_idle(),
            'idle_timeout': self.idle_timeout,
        }


class SourceSessionManager:
    """
    全局源会话管理器
    
    职责：
    - 维护全局 source_key -> SourceSession 映射
    - 提供 get_or_create_session() 接口
    - 管理订阅者的添加/移除
    - 定期清理空闲 session
    - 异常处理和日志
    """
    
    def __init__(self, idle_timeout: int = 5, cleanup_interval: int = 2):
        self._sessions: Dict[SourceKey, SourceSession] = {}
        self._lock = threading.RLock()
        self.idle_timeout = idle_timeout  # 前端用户关闭后5秒内停止session
        self.cleanup_interval = cleanup_interval  # 每2秒检查一次idle sessions
        
        # 启动清理线程
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        
        print(f"{get_timestamp()} [SourceSessionManager] Initialized with idle_timeout={idle_timeout}s, cleanup_interval={cleanup_interval}s", 
              flush=True)
    
    def get_or_create_session(self, source_key: SourceKey, stream, detector: PTDetector) -> SourceSession:
        """获取或创建一个会话"""
        with self._lock:
            if source_key in self._sessions:
                # 重用现有 session
                session = self._sessions[source_key]
                inf(f"[SESSION-REUSE] source_key={source_key} session_id={id(session)} ref_count={session.ref_count}")
                return session
            else:
                # 创建新 session
                session = SourceSession(source_key, stream, detector)
                session.idle_timeout = self.idle_timeout
                self._sessions[source_key] = session
                inf(f"[SESSION-CREATE] source_key={source_key} session_id={id(session)} stream_id={id(stream)} detector_id={id(detector)}")
                session.start()
                inf(f"[SESSION-START] source_key={source_key} session_id={id(session)} start_count={session.start_count}")
                return session
    
    def subscribe(self, source_key: SourceKey, ws) -> Optional[SourceSession]:
        """为 WebSocket 订阅一个 source"""
        with self._lock:
            if source_key in self._sessions:
                session = self._sessions[source_key]
                session.add_subscriber(ws)
                return session
        return None
    
    def unsubscribe(self, source_key: SourceKey, ws) -> bool:
        """取消订阅"""
        with self._lock:
            if source_key in self._sessions:
                session = self._sessions[source_key]
                session.remove_subscriber(ws)
                # 不立即删除，让 cleanup 线程处理
                return True
        return False
    
    def _cleanup_loop(self) -> None:
        """定期清理空闲 session"""
        inf("[SourceSessionManager] Cleanup thread started")
        
        try:
            while True:
                time.sleep(self.cleanup_interval)
                try:
                    self._cleanup_idle_sessions()
                except Exception as e:
                    wrn(f"[SourceSessionManager] Cleanup error: {e}")
        except Exception as e:
            err(f"[SourceSessionManager] Cleanup thread fatal error: {e}")
    
    def _cleanup_idle_sessions(self) -> None:
        """清理空闲的 session"""
        with self._lock:
            idle_keys = []
            for source_key, session in self._sessions.items():
                if session.is_idle():
                    idle_keys.append(source_key)
            
            for key in idle_keys:
                session = self._sessions.pop(key)
                try:
                    session.stop()
                    print(f"{get_timestamp()} [SourceSessionManager] Cleaned up idle session: {key}", 
                          flush=True)
                except Exception as e:
                    print(f"{get_timestamp()} [SourceSessionManager] Error cleaning session {key}: {e}", 
                          flush=True)
    
    def close_all(self) -> None:
        """关闭所有 session"""
        inf("[SourceSessionManager] Closing all sessions...")
        
        try:
            with self._lock:
                for session in list(self._sessions.values()):
                    try:
                        session.stop()
                    except Exception as e:
                        err(f"[SourceSessionManager] Error closing session: {e}")
                self._sessions.clear()
        except Exception as e:
            err(f"[SourceSessionManager] Error in close_all: {e}")
        
        inf("[SourceSessionManager] All sessions closed")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取全局统计信息"""
        with self._lock:
            sessions_stats = []
            for session in self._sessions.values():
                sessions_stats.append(session.get_stats())
            
            return {
                'total_sessions': len(self._sessions),
                'total_subscribers': sum(s['subscriber_count'] for s in sessions_stats),
                'sessions': sessions_stats
            }


# 全局单例
_session_manager: Optional[SourceSessionManager] = None


def get_session_manager() -> SourceSessionManager:
    """获取全局会话管理器"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SourceSessionManager(idle_timeout=60, cleanup_interval=10)
    return _session_manager
