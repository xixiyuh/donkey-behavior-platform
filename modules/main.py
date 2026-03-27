# modules/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager
from urllib.parse import unquote
from typing import Optional
import asyncio
import traceback
import threading
import queue
import time
import numpy as np
import cv2

import modules.config as C
from .detector_pt import PTDetector
from .streams import open_source
from .websocket_manager import WSManager
from .overlays import put_fps

from backend.api import router as farm_router

def get_detector():
    """为每个连接创建一个新的检测器实例"""
    detector = PTDetector(C.PT_MODEL_PATH)
    print("Detector initialized successfully for new connection", flush=True)
    return detector


# 全局检测器实例（仅用于预热）
_detector = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _detector
    print("Starting RK3588 Realtime Detector...")
    try:
        _detector = get_detector()
        # 预热模型
        dummy = (np.zeros((C.IMG_SIZE[1], C.IMG_SIZE[0], 3), dtype=np.uint8) + 127)
        try:
            _detector.infer_once(dummy)
            print("Detector pre-warmed successfully")
        except Exception as e:
            print(f"Warning: pre-warm failed: {e}")
    except Exception as e:
        print(f"Warning: Failed to pre-load detector: {e}")

    yield

    if _detector:
        try:
            if hasattr(_detector, 'release'):
                _detector.release()
            _detector = None
            print("Realtime Detector shutdown gracefully")
        except Exception as e:
            print(f"Warning during shutdown: {e}")


app = FastAPI(title="Realtime Detector", version="1.0.0", lifespan=lifespan)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
static_dir = C.BASE_DIR / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 添加后端路由
app.include_router(farm_router)

ws_manager = WSManager(max_fps=C.MAX_FPS)


@app.get("/")
async def index():
    html_path = C.BASE_DIR / "static" / "index.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return HTMLResponse(
        "<html><body><h3>Detector is running</h3><p>WebSocket: /ws</p></body></html>"
    )


@app.get("/health")
async def health_check():
    try:
        _ = get_detector()
        return {"status": "ok", "detector": "loaded"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


from fastapi import UploadFile, File
import os

import aiofiles

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # 确保上传目录存在
        upload_dir = C.BASE_DIR / "uploads"
        upload_dir.mkdir(exist_ok=True)
        
        # 保存文件（使用异步I/O）
        file_path = upload_dir / file.filename
        content = await file.read()
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        return {"success": True, "file_path": str(file_path)}
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.delete("/upload/{filename}")
async def delete_uploaded_file(filename: str):
    """删除已上传的文件"""
    try:
        upload_dir = C.BASE_DIR / "uploads"
        file_path = upload_dir / filename
        
        # 安全检查：确保文件路径在uploads目录内
        try:
            file_path.resolve().relative_to(upload_dir.resolve())
        except ValueError:
            return {"success": False, "message": "Invalid file path"}
        
        if file_path.exists():
            file_path.unlink()
            return {"success": True, "message": f"File {filename} deleted successfully"}
        else:
            return {"success": False, "message": f"File {filename} not found"}
    except Exception as e:
        return {"success": False, "message": str(e)}



def start_pipeline(stream, det: PTDetector, result_queue: queue.Queue, stop_event: threading.Event):
    frame_queue = queue.Queue(maxsize=C.QUEUE_MAX)

    def reader():
        cnt = 0
        last = time.time()
        consecutive_failures = 0
        max_consecutive_failures = 10  # 连续失败10次认为流已结束
        try:
            while not stop_event.is_set():
                ok, frame = stream.read()
                if ok and frame is not None:
                    cnt += 1
                    consecutive_failures = 0

                if time.time() - last > 1:
                    print(f"READER fps≈{cnt}, ok={ok}, frame={'None' if frame is None else frame.shape}", flush=True)
                    cnt = 0
                    last = time.time()

                if not ok or frame is None:
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        print("[READER] Stream ended, setting stop event", flush=True)
                        stop_event.set()
                        break
                    time.sleep(0.02)
                    continue

                # 丢旧帧：低延迟
                while not frame_queue.empty():
                    try:
                        frame_queue.get_nowait()
                    except queue.Empty:
                        break
                try:
                    frame_queue.put(frame, timeout=0.01)
                except queue.Full:
                    pass
        except Exception as e:
            print(f"READER thread error: {e}", flush=True)
        finally:
            print("READER thread stopped", flush=True)
            # 确保流资源被释放
            try:
                if hasattr(stream, 'release'):
                    stream.release()
                    print("[READER] Stream released in finally block", flush=True)
            except Exception as e:
                print(f"[READER] Error releasing stream in finally: {e}", flush=True)

    def infer():
        last_fps = 0.0
        idx = 0
        try:
            while not stop_event.is_set():
                try:
                    frame = frame_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                try:
                    do_infer = (idx % max(1, C.FRAME_INTERVAL) == 0)
                    if do_infer:
                        r, dt = det.infer_once(frame)
                        last_fps = 1.0 / dt if dt and dt > 0 else 0.0
                        # 传递camera_id、pen_id和barn_id参数
                        frame = det.annotate(frame, r, camera_id=stream.camera_id if hasattr(stream, 'camera_id') else None,
                                             pen_id=stream.pen_id if hasattr(stream, 'pen_id') else None,
                                             barn_id=stream.barn_id if hasattr(stream, 'barn_id') else None)

                    put_fps(frame, last_fps)

                except Exception as e:
                    warn = f"INFER ERROR: {type(e).__name__}: {e}"
                    print(warn, flush=True)
                    cv2.putText(frame, warn, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                # 只保留最新结果
                while not result_queue.empty():
                    try:
                        result_queue.get_nowait()
                    except queue.Empty:
                        break
                try:
                    result_queue.put(frame, timeout=0.01)
                except queue.Full:
                    pass

                idx += 1
        except Exception as e:
            print(f"INFER thread error: {e}", flush=True)
        finally:
            print("INFER thread stopped", flush=True)

    t_reader = threading.Thread(target=reader, daemon=True)
    t_infer = threading.Thread(target=infer, daemon=True)
    t_reader.start()
    t_infer.start()
    return t_reader, t_infer


@app.websocket("/ws")
async def ws_endpoint(
        ws: WebSocket,
        kind: str = Query("camera",
                          description="camera | file | rtsp | image | mpv | mpvpipe | rtmp | flv | hls | m3u8"),
        value: Optional[str] = Query(None, description="path/url/index"),
):
    await ws.accept()
    await ws_manager.register(ws)

    print(f"[WS] New connection: kind={kind}, value={value}", flush=True)

    stream = None
    stop_event = threading.Event()
    result_queue: queue.Queue = queue.Queue(maxsize=C.QUEUE_MAX)
    threads = None

    try:
        det = get_detector()

        # 前端是 urlencode 过的,这里必须 decode
        if value is not None:
            value = unquote(value)
        print(f"[WS] DECODED value = {value}", flush=True)

        # 异步打开视频源，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        stream = await loop.run_in_executor(None, lambda: open_source(kind, value or ""))

        # 启动处理线程
        threads = start_pipeline(stream, det, result_queue, stop_event)

        # 异步处理帧数据
        while True:
            try:
                # 使用非阻塞方式获取帧
                try:
                    frame = result_queue.get(block=False)
                except queue.Empty:
                    await asyncio.sleep(0.01)
                    continue

                # 异步发送帧数据
                await ws_manager.send_frame(ws, frame)

            except asyncio.CancelledError:
                break

    except WebSocketDisconnect:
        print("[WS] Client disconnected", flush=True)
    except Exception as e:
        print(f"[WS] Error: {type(e).__name__}: {e}", flush=True)
        try:
            await ws.send_text(f"ERROR::{repr(e)}\n{traceback.format_exc()}")
        except Exception:
            pass
    finally:
        print("[WS] Cleaning up...", flush=True)

        # 1. 停止后台线程
        stop_event.set()

        # 2. 等待线程结束（最多 2 秒）
        if threads:
            t_reader, t_infer = threads
            for t, name in [(t_reader, "reader"), (t_infer, "infer")]:
                if t and t.is_alive():
                    t.join(timeout=2.0)
                    if t.is_alive():
                        print(f"[WS] Warning: {name} thread still alive after timeout", flush=True)

        # 3. 释放流资源
        if stream:
            try:
                stream.release()
                print("[WS] Stream released", flush=True)
            except Exception as e:
                print(f"[WS] Error releasing stream: {e}", flush=True)

        # 4. 注销 WebSocket
        await ws_manager.unregister(ws)

        # 5. 关闭 WebSocket 连接
        try:
            await ws.close()
        except Exception:
            pass

        print("[WS] Cleanup complete", flush=True)
