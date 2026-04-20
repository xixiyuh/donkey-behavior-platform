# modules/websocket_manager.py
"""
WebSocket 管理器 - 优化版本检查和统一编码

关键改进：
1. 版本检查：只有当 display_version 变化时才发送
2. 统一编码：调用 session.encode_and_cache_jpeg() 进行统一编码
3. 避免重复编码：多个订阅者共享同一份已编码 JPEG
"""
import asyncio
import base64
import cv2
import time
import modules.config as C
from .logger import inf, dbg


class WSManager:
    def __init__(self, max_fps: float = 20):
        self.clients = set()
        self.interval = 1.0 / max_fps if max_fps > 0 else 0
        self._last_times = {}  # 为每个连接维护独立的时间戳
        self._last_display_versions = {}  # 为每个连接维护上一次发送的版本号

    async def register(self, ws):
        self.clients.add(ws)
        self._last_times[ws] = 0  # 初始化连接的时间戳
        self._last_display_versions[ws] = -1  # 初始化版本号
        print(f"WebSocket registered, total: {len(self.clients)}")

    async def unregister(self, ws):
        self.clients.discard(ws)
        self._last_times.pop(ws, None)  # 清理连接的时间戳
        self._last_display_versions.pop(ws, None)  # 清理版本号
        print(f"WebSocket unregistered, total: {len(self.clients)}")

    async def send_frame(self, ws, frame, session=None, jpeg_quality: int = None):
        """
        发送帧给 WebSocket 客户端
        
        改进：
        1. 支持版本检查（仅当display_version变化时才发送）
        2. 支持统一编码（调用session.encode_and_cache_jpeg()）
        3. 避免重复编码和重复发送
        
        Args:
            ws: WebSocket 连接
            frame: 帧数据（可选，如果session存在则忽略）
            session: SourceSession 对象（用于版本检查和统一编码）
            jpeg_quality: JPEG 质量（默认使用配置文件）
        """
        if jpeg_quality is None:
            jpeg_quality = C.JPEG_QUALITY
        
        now = time.time()
        last = self._last_times.get(ws, 0)
        
        # 检查是否超过发送间隔
        if self.interval > 0 and now - last < self.interval:
            await asyncio.sleep(self.interval - (now - last))
        
        # 如果有session，进行版本检查
        if session is not None:
            current_display_version = session.get_display_version()
            last_display_version = self._last_display_versions.get(ws, -1)
            
            # 版本未变化，不需要发送
            if current_display_version == last_display_version:
                return
            
            # 版本已变化，更新记录
            self._last_display_versions[ws] = current_display_version
            
            # 调用 session 进行统一编码和缓存
            jpeg_bytes, version = session.encode_and_cache_jpeg(quality=jpeg_quality)
            
            if jpeg_bytes is None:
                # 没有可用的显示帧
                return
            
            # 转成 Base64 字符串
            frame_data = base64.b64encode(jpeg_bytes).decode('utf-8')
        else:
            # 兼容旧代码：直接编码传入的frame
            try:
                loop = asyncio.get_event_loop()
                def encode_frame():
                    ok, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
                    if not ok:
                        raise RuntimeError("Failed to encode frame to JPEG")
                    return base64.b64encode(buffer).decode('utf-8')
                
                frame_data = await loop.run_in_executor(None, encode_frame)
            except Exception as e:
                dbg(f"Frame encoding error: {e}")
                raise RuntimeError(f"Failed to encode frame: {e}") from e
        
        self._last_times[ws] = time.time()
        
        try:
            await ws.send_text(frame_data)
        except Exception as e:
            # WebSocket 已断开或发送失败
            raise RuntimeError(f"WebSocket send failed: {e}") from e
