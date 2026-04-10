# modules/websocket_manager.py
import asyncio
import base64
import cv2
import time
import modules.config as C


class WSManager:
    def __init__(self, max_fps: float = 20):
        self.clients = set()
        self.interval = 1.0 / max_fps if max_fps > 0 else 0
        self._last_times = {}  # 为每个连接维护独立的时间戳

    async def register(self, ws):
        self.clients.add(ws)
        self._last_times[ws] = 0  # 初始化连接的时间戳
        print(f"WebSocket registered, total: {len(self.clients)}")

    async def unregister(self, ws):
        self.clients.discard(ws)
        self._last_times.pop(ws, None)  # 清理连接的时间戳
        print(f"WebSocket unregistered, total: {len(self.clients)}")

    async def send_frame(self, ws, frame):
        now = time.time()
        last = self._last_times.get(ws, 0)
        # 如果没到发送间隔，就等一下，避免发送过快
        if self.interval > 0 and now - last < self.interval:
            await asyncio.sleep(self.interval - (now - last))
        self._last_times[ws] = time.time()

        # 使用异步方式执行编码操作，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        def encode_frame():
            ok, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, C.JPEG_QUALITY])
            if not ok:
                raise RuntimeError("Failed to encode frame to JPEG")
            # 转成 Base64 字符串（前端可以直接放在 img src 里显示）
            return base64.b64encode(buffer).decode('utf-8')

        frame_data = await loop.run_in_executor(None, encode_frame)

        try:
            await ws.send_text(frame_data)
        except Exception as e:
            # WebSocket 已断开或发送失败，抛出异常以终止主循环
            raise RuntimeError(f"WebSocket send failed: {e}") from e