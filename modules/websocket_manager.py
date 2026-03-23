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
        self._last = 0

    async def register(self, ws):
        self.clients.add(ws)
        print(f"WebSocket registered, total: {len(self.clients)}")

    async def unregister(self, ws):
        self.clients.discard(ws)
        print(f"WebSocket unregistered, total: {len(self.clients)}")

    async def send_frame(self, ws, frame):
        now = time.time()
        if self.interval > 0 and now - self._last < self.interval:
            await asyncio.sleep(self.interval - (now - self._last))
        self._last = time.time()

        ok, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, C.JPEG_QUALITY])
        if not ok:
            raise RuntimeError("Failed to encode frame to JPEG")
        frame_data = base64.b64encode(buffer).decode('utf-8')

        try:
            await ws.send_text(frame_data)
        except Exception as e:
            # WebSocket 已断开或发送失败，抛出异常以终止主循环
            raise RuntimeError(f"WebSocket send failed: {e}") from e