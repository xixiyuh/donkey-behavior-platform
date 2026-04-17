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

# 导入定时任务库
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

# 生成时间戳格式
def get_timestamp():
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

import modules.config as C
from .detector_pt import PTDetector
from .streams import open_source
from .websocket_manager import WSManager
from .overlays import put_fps
from .stream_manager import get_stream_manager

from backend.apis import router as farm_router, register_start_detection_func, register_stop_detection_func
from backend.models import CameraConfig
from backend.database import init_db

def get_detector():
    """为每个连接创建一个新的检测器实例"""
    detector = PTDetector(C.PT_MODEL_PATH)
    print(f"{get_timestamp()} Detector initialized successfully for new connection", flush=True)
    return detector


# 全局检测器实例（仅用于预热）
_detector = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _detector
    print(f"{get_timestamp()} Starting RK3588 Realtime Detector...")
    try:
        # 初始化数据库
        try:
            init_db()
            print(f"{get_timestamp()} Database initialized successfully")
        except Exception as e:
            print(f"{get_timestamp()} Warning: Database initialization failed (MySQL may not be available): {e}")
        
        # 初始化流管理器
        stream_mgr = get_stream_manager()
        print(f"{get_timestamp()} Stream manager initialized")
        
        _detector = get_detector()
        # 预热模型
        dummy = (np.zeros((C.IMG_SIZE[1], C.IMG_SIZE[0], 3), dtype=np.uint8) + 127)
        try:
            _detector.infer_once(dummy)
            print(f"{get_timestamp()} Detector pre-warmed successfully")
        except Exception as e:
            print(f"{get_timestamp()} Warning: pre-warm failed: {e}")
        
        # 启动调度器
        print(f"{get_timestamp()} Starting scheduler...")
        # 每天9:00启动检测
        scheduler.add_job(
            start_all_detections,
            CronTrigger(hour=9, minute=0),
            id='start_detection',
            replace_existing=True
        )
        # 每天19:00停止检测
        scheduler.add_job(
            stop_all_detections,
            CronTrigger(hour=19, minute=0),
            id='stop_detection',
            replace_existing=True
        )
        scheduler.start()
        print(f"{get_timestamp()} Scheduler started successfully")
        
        # 立即启动所有启用的摄像头检测
        print(f"{get_timestamp()} Starting all enabled camera detections immediately...")
        start_all_detections()
    except Exception as e:
        print(f"{get_timestamp()} Warning: Failed to pre-load detector: {e}")

    yield

    # 停止调度器
    print(f"{get_timestamp()} Stopping scheduler...")
    try:
        scheduler.shutdown()
        print(f"{get_timestamp()} Scheduler stopped successfully")
    except Exception as e:
        print(f"{get_timestamp()} Warning during scheduler shutdown: {e}")

    # 关闭所有流
    try:
        stream_mgr = get_stream_manager()
        stream_mgr.close_all()
        print(f"{get_timestamp()} Stream manager closed")
    except Exception as e:
        print(f"{get_timestamp()} Warning during stream manager shutdown: {e}")

    if _detector:
        try:
            if hasattr(_detector, 'release'):
                _detector.release()
            _detector = None
            print(f"{get_timestamp()} Realtime Detector shutdown gracefully")
        except Exception as e:
            print(f"{get_timestamp()} Warning during shutdown: {e}")


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

# 后台调度器
scheduler = BackgroundScheduler()

# 摄像头检测管理
class CameraDetectionManager:
    def __init__(self):
        self.active_detections = {}  # 存储 (thread, stop_event) 元组
        self.lock = threading.Lock()
    
    def start_detection(self, camera_config):
        """启动单个摄像头的检测"""
        config_id = camera_config['id']
        
        with self.lock:
            if config_id in self.active_detections:
                print(f"{get_timestamp()} [Detection] Camera {config_id} is already running")
                return
        
        # 创建检测线程
        stop_event = threading.Event()
        
        def detection_thread():
            print(f"{get_timestamp()} [Detection] Starting detection for camera {config_id}: {camera_config['camera_id']}")
            
            stream = None
            result_queue = queue.Queue(maxsize=C.QUEUE_MAX)
            
            def is_within_time_range():
                """判断当前时间是否在摄像头配置的时间范围内"""
                current_time = datetime.now().time()
                start_time = datetime.strptime(camera_config.get('start_time', '09:00'), '%H:%M').time()
                end_time = datetime.strptime(camera_config.get('end_time', '19:00'), '%H:%M').time()
                return start_time <= current_time <= end_time
            
            def reconnect():
                """尝试重新连接视频流"""
                nonlocal stream
                try:
                    print(f"{get_timestamp()} [Detection] Attempting to reconnect to camera {config_id}")
                    stream = open_source('flv', camera_config['flv_url'])
                    # 设置摄像头、栏和舍的ID
                    stream.camera_id = camera_config['camera_id']
                    stream.pen_id = camera_config['pen_id']
                    stream.barn_id = camera_config['barn_id']
                    return True
                except Exception as e:
                    print(f"{get_timestamp()} [Detection] Reconnection failed for camera {config_id}: {e}")
                    return False
            
            try:
                det = get_detector()
                stream = open_source('flv', camera_config['flv_url'])
                
                # 设置摄像头、栏和舍的ID
                stream.camera_id = camera_config['camera_id']
                stream.pen_id = camera_config['pen_id']
                stream.barn_id = camera_config['barn_id']
                
                # 启动处理线程
                t_reader, t_infer = start_pipeline(stream, det, result_queue, stop_event, camera_config)

                
                # 持续运行，直到停止事件被设置
                while not stop_event.is_set():
                    time.sleep(1)
                    
            except Exception as e:
                print(f"{get_timestamp()} [Detection] Error for camera {config_id}: {e}")
                
                # 自动重连逻辑
                reconnect_attempts = 0
                max_reconnect_attempts = 4
                
                # 第一次重连：10秒间隔，最多4次
                while reconnect_attempts < max_reconnect_attempts and not stop_event.is_set():
                    if not is_within_time_range():
                        print(f"{get_timestamp()} [Detection] Camera {config_id} is outside time range, stopping reconnection")
                        break
                    
                    print(f"{get_timestamp()} [Detection] Attempting to reconnect ({reconnect_attempts + 1}/{max_reconnect_attempts})...")
                    time.sleep(10)  # 等待10秒
                    
                    if reconnect():
                        print(f"{get_timestamp()} [Detection] Reconnection successful for camera {config_id}")
                        # 重新启动处理线程
                        t_reader, t_infer = start_pipeline(stream, det, result_queue, stop_event, camera_config)
                        # 继续运行
                        while not stop_event.is_set():
                            time.sleep(1)
                        break
                    
                    reconnect_attempts += 1
                
                # 如果第一次重连失败，等待1小时后进行第二次重连
                if reconnect_attempts >= max_reconnect_attempts and not stop_event.is_set():
                    print(f"{get_timestamp()} [Detection] All initial reconnection attempts failed for camera {config_id}, waiting 1 hour...")
                    time.sleep(3600)  # 等待1小时
                    
                    # 第二次重连：10秒间隔，最多3次
                    reconnect_attempts = 0
                    max_reconnect_attempts = 3
                    
                    while reconnect_attempts < max_reconnect_attempts and not stop_event.is_set():
                        if not is_within_time_range():
                            print(f"{get_timestamp()} [Detection] Camera {config_id} is outside time range, stopping reconnection")
                            break
                        
                        print(f"{get_timestamp()} [Detection] Attempting to reconnect after 1 hour ({reconnect_attempts + 1}/{max_reconnect_attempts})...")
                        time.sleep(10)  # 等待10秒
                        
                        if reconnect():
                            print(f"{get_timestamp()} [Detection] Reconnection successful for camera {config_id}")
                            # 重新启动处理线程
                            t_reader, t_infer = start_pipeline(stream, det, result_queue, stop_event, camera_config)
                            # 继续运行
                            while not stop_event.is_set():
                                time.sleep(1)
                            break
                        
                        reconnect_attempts += 1
            finally:
                print(f"{get_timestamp()} [Detection] Stopping detection for camera {config_id}")
                
                # 停止后台线程
                stop_event.set()
                
                # 释放流资源
                if stream:
                    try:
                        stream.release()
                    except Exception as e:
                        print(f"{get_timestamp()} [Detection] Error releasing stream: {e}")
                
                with self.lock:
                    if config_id in self.active_detections:
                        del self.active_detections[config_id]
        
        # 启动检测线程
        thread = threading.Thread(target=detection_thread, daemon=True)
        thread.start()
        
        with self.lock:
            self.active_detections[config_id] = (thread, stop_event)
        
        print(f"{get_timestamp()} [Detection] Started detection for camera {config_id}")
    
    def stop_detection(self, config_id):
        """停止单个摄像头的检测"""
        with self.lock:
            if config_id in self.active_detections:
                thread, stop_event = self.active_detections[config_id]
                stop_event.set()
                print(f"{get_timestamp()} [Detection] Stopping camera {config_id}")
    
    def stop_all_detections(self):
        """停止所有摄像头的检测"""
        with self.lock:
            config_ids = list(self.active_detections.keys())
        
        for config_id in config_ids:
            self.stop_detection(config_id)
        
        print(f"{get_timestamp()} [Detection] Stopped all detections")

# 创建摄像头检测管理器
detection_manager = CameraDetectionManager()

# 注册启动检测的函数
def start_detection_wrapper(config):
    """启动检测的包装函数"""
    detection_manager.start_detection(config)

# 注册停止检测的函数
def stop_detection_wrapper(config_id):
    """停止检测的包装函数"""
    detection_manager.stop_detection(config_id)

# 注册到后端API
register_start_detection_func(start_detection_wrapper)
register_stop_detection_func(stop_detection_wrapper)

# 定时任务函数
def start_all_detections():
    """启动所有应该激活的摄像头检测"""
    print(f"{get_timestamp()} [Scheduler] Starting all detections")
    
    try:
        configs = CameraConfig.get_active()
        print(f"{get_timestamp()} [Scheduler] Found {len(configs)} active cameras")
        
        for config in configs:
            detection_manager.start_detection(config)
    except Exception as e:
        print(f"{get_timestamp()} [Scheduler] Error starting detections: {e}")

def stop_all_detections():
    """停止所有摄像头检测"""
    print(f"{get_timestamp()} [Scheduler] Stopping all detections")
    detection_manager.stop_all_detections()


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


@app.get("/stream-stats")
async def get_stream_statistics():
    """获取流管理器的统计信息 - 查看当前流的使用情况和引用计数"""
    try:
        stream_mgr = get_stream_manager()
        stats = stream_mgr.get_stats()
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "streams": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


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


@app.post("/api/camera-configs/{config_id}/stop")
async def stop_camera_detection(config_id: int):
    """立即停止指定摄像头的检测任务"""
    try:
        print(f"{get_timestamp()} [API] Stopping camera detection for config ID: {config_id}")
        detection_manager.stop_detection(config_id)
        return {"success": True, "message": f"Camera detection stopped for config ID {config_id}"}
    except Exception as e:
        print(f"{get_timestamp()} [API] Error stopping camera detection: {e}")
        return {"success": False, "message": str(e)}



def start_pipeline(stream, det: PTDetector, result_queue: queue.Queue, stop_event: threading.Event, camera_config=None):
    frame_queue = queue.Queue(maxsize=C.QUEUE_MAX)

    def is_within_time_range():
        """判断当前时间是否在摄像头配置的时间范围内"""
        if not camera_config:
            return True
        current_time = datetime.now().time()
        start_time = datetime.strptime(camera_config.get('start_time', '09:00'), '%H:%M').time()
        end_time = datetime.strptime(camera_config.get('end_time', '19:00'), '%H:%M').time()
        return start_time <= current_time <= end_time

    def reconnect():
        """尝试重新连接视频流"""
        nonlocal stream
        try:
            print(f"{get_timestamp()} [READER] Attempting to reconnect to camera {camera_config.get('id', 'unknown')}")
            stream = open_source('flv', camera_config['flv_url'])
            # 设置摄像头、栏和舍的ID
            stream.camera_id = camera_config['camera_id']
            stream.pen_id = camera_config['pen_id']
            stream.barn_id = camera_config['barn_id']
            return True
        except Exception as e:
            print(f"{get_timestamp()} [READER] Reconnection failed: {e}")
            return False

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
                    print(f"{get_timestamp()} READER fps≈{cnt}, ok={ok}, frame={'None' if frame is None else frame.shape}", flush=True)
                    cnt = 0
                    last = time.time()

                if not ok or frame is None:
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        print(f"{get_timestamp()} [READER] Stream ended, checking reconnection conditions", flush=True)
                        # 检查是否处于工作时间且摄像头状态不是禁用
                        if camera_config and is_within_time_range() and camera_config.get('status', 'enabled') == 'enabled':
                            print(f"{get_timestamp()} [READER] Attempting to reconnect", flush=True)
                            # 尝试重新连接
                            if reconnect():
                                print(f"{get_timestamp()} [READER] Reconnection successful, continuing", flush=True)
                                consecutive_failures = 0
                                time.sleep(0.1)  # 短暂等待，确保流稳定
                                continue
                            else:
                                print(f"{get_timestamp()} [READER] Reconnection failed, setting stop event", flush=True)
                                stop_event.set()
                                break
                        else:
                            print(f"{get_timestamp()} [READER] Not in working time or camera disabled, setting stop event", flush=True)
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
            print(f"{get_timestamp()} READER thread error: {e}", flush=True)
        finally:
            print(f"{get_timestamp()} READER thread stopped", flush=True)
            # 确保流资源被释放
            try:
                if hasattr(stream, 'release'):
                    stream.release()
                    print(f"{get_timestamp()} [READER] Stream released in finally block", flush=True)
            except Exception as e:
                print(f"{get_timestamp()} [READER] Error releasing stream in finally: {e}", flush=True)

    def infer():
        last_fps = 0.0
        idx = 0
        last_r = None  # 保存上一次的推理结果
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
                        last_r = r  # 保存推理结果
                        last_fps = 1.0 / dt if dt and dt > 0 else 0.0
                        # 传递camera_id、pen_id和barn_id参数
                        frame = det.annotate(frame, r, camera_id=stream.camera_id if hasattr(stream, 'camera_id') else None,
                                             pen_id=stream.pen_id if hasattr(stream, 'pen_id') else None,
                                             barn_id=stream.barn_id if hasattr(stream, 'barn_id') else None)
                    else:
                        # 使用上一次的推理结果绘制检测框
                        if last_r is not None:
                            frame = det.annotate(frame, last_r, camera_id=stream.camera_id if hasattr(stream, 'camera_id') else None,
                                                 pen_id=stream.pen_id if hasattr(stream, 'pen_id') else None,
                                                 barn_id=stream.barn_id if hasattr(stream, 'barn_id') else None)

                    put_fps(frame, last_fps)

                except Exception as e:
                    warn = f"INFER ERROR: {type(e).__name__}: {e}"
                    print(f"{get_timestamp()} {warn}", flush=True)
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
            print(f"{get_timestamp()} INFER thread error: {e}", flush=True)
        finally:
            print(f"{get_timestamp()} INFER thread stopped", flush=True)

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
        camera_id: Optional[str] = Query(None, description="Camera ID"),
        pen_id: Optional[int] = Query(None, description="Pen ID"),
        barn_id: Optional[int] = Query(None, description="Barn ID"),
):
    await ws.accept()
    await ws_manager.register(ws)

    print(f"{get_timestamp()} [WS] New connection: kind={kind}, value={value}, camera_id={camera_id}, pen_id={pen_id}, barn_id={barn_id}", flush=True)

    stream = None
    stream_key = None
    stop_event = threading.Event()
    result_queue: queue.Queue = queue.Queue(maxsize=C.QUEUE_MAX)
    threads = None

    try:
        det = get_detector()

        # 前端是 urlencode 过的,这里必须 decode
        if value is not None:
            value = unquote(value)
        print(f"{get_timestamp()} [WS] DECODED value = {value}", flush=True)

        # 使用流管理器获取流 - 支持流复用和引用计数
        stream_mgr = get_stream_manager()
        loop = asyncio.get_event_loop()
        stream, stream_key = await loop.run_in_executor(
            None, 
            lambda: stream_mgr.get_stream(kind, value or "")
        )
        
        # 设置摄像头、栏和舍的ID
        if camera_id:
            stream.camera_id = camera_id
        if pen_id:
            stream.pen_id = pen_id
        if barn_id:
            stream.barn_id = barn_id
        print(f"{get_timestamp()} [WS] Stream configured: camera_id={stream.camera_id if hasattr(stream, 'camera_id') else None}, pen_id={stream.pen_id if hasattr(stream, 'pen_id') else None}, barn_id={stream.barn_id if hasattr(stream, 'barn_id') else None}", flush=True)

        # 启动处理线程
        # 对于WebSocket连接，没有camera_config，所以传递None
        threads = start_pipeline(stream, det, result_queue, stop_event, None)

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
        print(f"{get_timestamp()} [WS] Client disconnected", flush=True)
    except Exception as e:
        print(f"{get_timestamp()} [WS] Error: {type(e).__name__}: {e}", flush=True)
        try:
            await ws.send_text(f"ERROR::{repr(e)}\n{traceback.format_exc()}")
        except Exception:
            pass
    finally:
        print(f"{get_timestamp()} [WS] Cleaning up...", flush=True)

        # 1. 停止后台线程
        stop_event.set()

        # 2. 等待线程结束（最多 2 秒）
        if threads:
            t_reader, t_infer = threads
            for t, name in [(t_reader, "reader"), (t_infer, "infer")]:
                if t and t.is_alive():
                    t.join(timeout=2.0)
                    if t.is_alive():
                        print(f"{get_timestamp()} [WS] Warning: {name} thread still alive after timeout", flush=True)

        # 3. 使用流管理器释放流 - 只有当引用计数为0时才真正释放资源
        if stream_key:
            try:
                stream_mgr = get_stream_manager()
                stream_mgr.release_stream(stream_key)
                print(f"{get_timestamp()} [WS] Stream released and managed by stream manager", flush=True)
            except Exception as e:
                print(f"{get_timestamp()} [WS] Error releasing stream: {e}", flush=True)

        # 4. 注销 WebSocket
        await ws_manager.unregister(ws)

        # 5. 关闭 WebSocket 连接
        try:
            await ws.close()
        except Exception:
            pass

        print(f"{get_timestamp()} [WS] Cleanup complete", flush=True)
