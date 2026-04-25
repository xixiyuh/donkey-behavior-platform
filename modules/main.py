# modules/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
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
from backend.config import settings
from .detector_pt import PTDetector
from .streams import open_source
from .websocket_manager import WSManager
from .overlays import put_fps
from .stream_manager import get_stream_manager
from .source_session_manager import get_session_manager, SourceKey

from backend.apis import router as farm_router, register_start_detection_func, register_stop_detection_func
from backend.models import CameraConfig
from backend.services import cleanup_expired_mating_events
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
        
        # 初始化流管理器（裸流共享）
        stream_mgr = get_stream_manager()
        print(f"{get_timestamp()} Stream manager initialized")
        
        # 初始化会话管理器（完整 pipeline 共享）
        session_mgr = get_session_manager()
        print(f"{get_timestamp()} Source session manager initialized")
        
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
        # 每天凌晨清理上传文件
        scheduler.add_job(
            cleanup_uploaded_files,
            CronTrigger(hour=C.UPLOAD_CLEANUP_HOUR, minute=C.UPLOAD_CLEANUP_MINUTE),
            id='cleanup_uploads',
            replace_existing=True
        )
        scheduler.add_job(
            cleanup_expired_events,
            CronTrigger(
                hour=getattr(C, "EVENT_RETENTION_CLEANUP_HOUR", 2),
                minute=getattr(C, "EVENT_RETENTION_CLEANUP_MINUTE", 0)
            ),
            id='cleanup_expired_events',
            replace_existing=True
        )
        scheduler.start()
        print(f"{get_timestamp()} Scheduler started successfully")
        
        # 立即启动所有启用的摄像头检测
        print(f"{get_timestamp()} Starting all enabled camera detections immediately...")
        start_all_detections()
        # 立即执行一次清理（方便测试）
        cleanup_uploaded_files()
        cleanup_expired_events()
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

    # 关闭所有会话
    try:
        session_mgr = get_session_manager()
        session_mgr.close_all()
        print(f"{get_timestamp()} Source session manager closed")
    except Exception as e:
        print(f"{get_timestamp()} Warning during session manager shutdown: {e}")
    
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
    allow_origins=settings.allowed_origins,
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
    """
    摄像头定时检测管理器
    
    改造要点：
    - 使用 SourceSessionManager 来管理 pipeline
    - 最小化改动，保留重连逻辑
    - 与 WebSocket 用户共享同一路摄像头的 pipeline
    """
    
    def __init__(self):
        self.active_detections = {}  # 存储 (thread, stop_event, source_key) 元组
        self.lock = threading.Lock()
        self.session_mgr = get_session_manager()
    
    def start_detection(self, camera_config):
        """启动单个摄像头的检测"""
        camera_config = dict(camera_config)  # 确保是字典类型
        config_id = camera_config['id']
        flv_url = camera_config['flv_url']
        camera_id = camera_config.get('camera_id')
        
        with self.lock:
            if config_id in self.active_detections:
                print(f"{get_timestamp()} [Detection] Camera {config_id} is already running")
                return
        
        # 创建检测线程
        stop_event = threading.Event()
        
        # 生成 source key - 注意：这里使用 camera_id 而不是 value，确保相同摄像头共用 session
        source_key = SourceKey(kind='flv', value=flv_url, camera_id=camera_id, pen_id=camera_config.get('pen_id'), barn_id=camera_config.get('barn_id'))
        
        def detection_thread():
            print(f"{get_timestamp()} [Detection] Starting detection for camera {config_id}: {camera_id} ({flv_url[:50]}...)")
            
            session = None
            task_subscriber = f"scheduled_task_{config_id}"
            
            def is_within_time_range():
                """判断当前时间是否在摄像头配置的时间范围内"""
                try:
                    current_time = datetime.now().time()
                    start_time = datetime.strptime(camera_config.get('start_time', '00:00'), '%H:%M').time()
                    end_time = datetime.strptime(camera_config.get('end_time', '23:59'), '%H:%M').time()
                    
                    # 处理跨午夜的情况
                    if start_time <= end_time:
                        return start_time <= current_time <= end_time
                    else:
                        return current_time >= start_time or current_time <= end_time
                except Exception as e:
                    print(f"{get_timestamp()} [Detection] Error checking time range: {e}")
                    return True  # 遇到错误时允许运行
            
            def try_reconnect():
                """双阶段重连机制"""
                nonlocal session
                
                # 第一阶段：10秒间隔最多4次
                first_stage_retries = 4
                for attempt in range(1, first_stage_retries + 1):
                    if stop_event.is_set():
                        print(f"{get_timestamp()} [Reconnect] Stage 1 cancelled for camera {config_id}")
                        return None
                    
                    if not is_within_time_range():
                        print(f"{get_timestamp()} [Reconnect] Camera {config_id} outside working hours, deferring")
                        return None
                    
                    try:
                        print(f"{get_timestamp()} [Reconnect] Stage 1 - Attempt {attempt}/{first_stage_retries} for camera {config_id}")
                        
                        # 创建新的流对象
                        stream = open_source('flv', flv_url)
                        stream.camera_id = camera_id
                        stream.pen_id = camera_config.get('pen_id')
                        stream.barn_id = camera_config.get('barn_id')
                        
                        detector = PTDetector(C.PT_MODEL_PATH)
                        
                        # 从 session manager 获取或创建 session
                        session = self.session_mgr.get_or_create_session(source_key, stream, detector)
                        
                        # 注册为订阅者
                        session.add_subscriber(task_subscriber)
                        
                        print(f"{get_timestamp()} [Reconnect] Stage 1 - Successfully connected camera {config_id}")
                        
                        # 验证推理线程是否启动并运行
                        stats = session.get_stats()
                        if stats.get('infer_alive', False):
                            return session
                        
                        # 如果推理线程没有启动，继续重试
                        session.remove_subscriber(task_subscriber)
                        
                    except Exception as e:
                        print(f"{get_timestamp()} [Reconnect] Stage 1 - Connection failed (attempt {attempt}): {e}")
                    
                    # 等待10秒后重试
                    time.sleep(10)
                
                # 第一阶段失败，进入第二阶段
                print(f"{get_timestamp()} [Reconnect] Stage 1 exhausted for camera {config_id}, entering Stage 2")
                
                # 第二阶段：先等待1小时
                wait_minutes = 60
                for remaining in range(wait_minutes, 0, -1):
                    if stop_event.is_set():
                        print(f"{get_timestamp()} [Reconnect] Stage 2 wait cancelled for camera {config_id}")
                        return None
                    
                    if remaining % 10 == 0 or remaining <= 5:  # 每10分钟打印一次，最后5分钟每分钟打印
                        print(f"{get_timestamp()} [Reconnect] Stage 2 - Waiting {remaining} minutes before retrying camera {config_id}")
                    
                    time.sleep(60)
                
                # 第二阶段：再按10秒间隔额外尝试3次
                second_stage_retries = 3
                for attempt in range(1, second_stage_retries + 1):
                    if stop_event.is_set():
                        print(f"{get_timestamp()} [Reconnect] Stage 2 cancelled for camera {config_id}")
                        return None
                    
                    if not is_within_time_range():
                        print(f"{get_timestamp()} [Reconnect] Camera {config_id} outside working hours, giving up")
                        return None
                    
                    try:
                        print(f"{get_timestamp()} [Reconnect] Stage 2 - Attempt {attempt}/{second_stage_retries} for camera {config_id}")
                        
                        stream = open_source('flv', flv_url)
                        stream.camera_id = camera_id
                        stream.pen_id = camera_config.get('pen_id')
                        stream.barn_id = camera_config.get('barn_id')
                        
                        detector = PTDetector(C.PT_MODEL_PATH)
                        
                        session = self.session_mgr.get_or_create_session(source_key, stream, detector)
                        session.add_subscriber(task_subscriber)
                        
                        print(f"{get_timestamp()} [Reconnect] Stage 2 - Successfully connected camera {config_id}")
                        
                        # 验证推理线程是否启动并运行
                        stats = session.get_stats()
                        if stats.get('infer_alive', False):
                            return session
                        
                        session.remove_subscriber(task_subscriber)
                        
                    except Exception as e:
                        print(f"{get_timestamp()} [Reconnect] Stage 2 - Connection failed (attempt {attempt}): {e}")
                    
                    time.sleep(10)
                
                print(f"{get_timestamp()} [Reconnect] Stage 2 exhausted for camera {config_id}, giving up permanently")
                return None
            
            try:
                # 初始连接（使用重连逻辑）
                session = try_reconnect()
                
                if session is None:
                    print(f"{get_timestamp()} [Detection] Failed to establish connection for camera {config_id}")
                    return
                
                print(f"{get_timestamp()} [Detection] Registered scheduled task as subscriber for {source_key}")
                
                # 持续运行，直到停止事件被设置
                last_check_time = time.time()
                while not stop_event.is_set():
                    try:
                        # 定期检查是否在工作时间内
                        current_time = time.time()
                        if current_time - last_check_time > 300:  # 每5分钟检查一次时间范围
                            if not is_within_time_range():
                                print(f"{get_timestamp()} [Detection] Camera {config_id} is outside time range, pausing")
                                time.sleep(60)
                                continue
                            last_check_time = current_time
                        
                        # 检查session是否仍然有效（检查推理线程是否活着）
                        stats = session.get_stats()
                        if not stats.get('infer_alive', False) and not stop_event.is_set():
                            print(f"{get_timestamp()} [Detection] Inference thread died for camera {config_id}, attempting reconnection")
                            session.remove_subscriber(task_subscriber)
                            session = try_reconnect()
                            if session is None:
                                print(f"{get_timestamp()} [Detection] Reconnection failed for camera {config_id}")
                                break
                        
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"{get_timestamp()} [Detection] Error monitoring camera {config_id}: {e}")
                        if not stop_event.is_set():
                            print(f"{get_timestamp()} [Detection] Attempting reconnection for camera {config_id}")
                            try:
                                session.remove_subscriber(task_subscriber)
                            except:
                                pass
                            session = try_reconnect()
                            if session is None:
                                break
                        
            except Exception as e:
                print(f"{get_timestamp()} [Detection] Fatal error for camera {config_id}: {e}")
                    
            finally:
                print(f"{get_timestamp()} [Detection] Stopping detection for camera {config_id}")
                
                # 结束该摄像头的所有standing事件
                try:
                    from .detector_pt import get_mating_detector
                    mating_detector = get_mating_detector()
                    camera_key = camera_config.get('camera_id', 'unknown') if camera_config else 'unknown'
                    pen_id = camera_config.get('pen_id', -1) if camera_config else -1
                    barn_id = camera_config.get('barn_id', -1) if camera_config else -1
                    mating_detector.end_all_events(camera_key=camera_key, pen_id=pen_id, barn_id=barn_id)
                except Exception as e:
                    print(f"{get_timestamp()} [Detection] Error ending events: {e}")
                
                # 取消注册订阅并释放资源
                if session:
                    try:
                        session.remove_subscriber(task_subscriber)
                        print(f"{get_timestamp()} [Detection] Unregistered scheduled task from {source_key}")
                    except Exception as e:
                        print(f"{get_timestamp()} [Detection] Error unregistering: {e}")
                
                with self.lock:
                    if config_id in self.active_detections:
                        del self.active_detections[config_id]
        
        # 启动检测线程
        thread = threading.Thread(target=detection_thread, daemon=True)
        thread.start()
        
        with self.lock:
            self.active_detections[config_id] = (thread, stop_event, source_key)
        
        print(f"{get_timestamp()} [Detection] Started detection for camera {config_id}")
    
    def stop_detection(self, config_id):
        """停止单个摄像头的检测"""
        with self.lock:
            if config_id in self.active_detections:
                thread, stop_event, source_key = self.active_detections[config_id]
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

def cleanup_uploaded_files():
    """清理上传的过期文件"""
    print(f"{get_timestamp()} [Scheduler] Starting upload files cleanup")
    
    try:
        upload_dir = settings.upload_dir
        if not upload_dir.exists():
            print(f"{get_timestamp()} [Scheduler] Upload directory not found")
            return
        
        current_time = time.time()
        retention_seconds = C.UPLOAD_FILE_RETENTION_HOURS * 3600
        deleted_count = 0
        checked_count = 0
        
        for file_path in upload_dir.iterdir():
            if file_path.is_file():
                checked_count += 1
                file_age = current_time - file_path.stat().st_mtime
                file_age_hours = file_age / 3600
                print(f"{get_timestamp()} [Scheduler] File: {file_path.name}, age: {file_age_hours:.1f}h, retention: {C.UPLOAD_FILE_RETENTION_HOURS}h", flush=True)
                
                if file_age > retention_seconds:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        print(f"{get_timestamp()} [Scheduler] Deleted expired file: {file_path.name}")
                    except Exception as e:
                        print(f"{get_timestamp()} [Scheduler] Error deleting file {file_path.name}: {e}")
        
        print(f"{get_timestamp()} [Scheduler] Upload cleanup completed. Checked: {checked_count}, Deleted: {deleted_count} files")
    except Exception as e:
        print(f"{get_timestamp()} [Scheduler] Error during upload cleanup: {e}")


def cleanup_expired_events():
    """Clean up expired mating events and their screenshots."""
    print(f"{get_timestamp()} [Scheduler] Starting expired events cleanup")

    try:
        result = cleanup_expired_mating_events(
            retention_months=getattr(C, "EVENT_RETENTION_MONTHS", 3)
        )
        print(
            f"{get_timestamp()} [Scheduler] Expired events cleanup completed. "
            f"Retention: {result['retention_months']} months, "
            f"Matched: {result['expired_events']}, "
            f"Deleted events: {result['deleted_events']}, "
            f"Deleted files: {result['deleted_files']}, "
            f"Missing files: {result['missing_files']}, "
            f"Skipped files: {result['skipped_files']}, "
            f"File errors: {result['file_errors']}"
        )
    except Exception as e:
        print(f"{get_timestamp()} [Scheduler] Error during expired events cleanup: {e}")


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


@app.get("/session-stats")
async def get_session_statistics():
    """获取会话管理器统计信息 - 查看当前 session 的使用情况和订阅者数量"""
    try:
        session_mgr = get_session_manager()
        stats = session_mgr.get_stats()
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "sessions": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


from fastapi import UploadFile, File
import os
from pathlib import Path
import uuid

import aiofiles

UPLOAD_CHUNK_SIZE = 1024 * 1024
IMAGE_MAX_UPLOAD_SIZE = settings.image_max_upload_size
VIDEO_MAX_UPLOAD_SIZE = settings.video_max_upload_size
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
ALLOWED_UPLOAD_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS
ALLOWED_UPLOAD_MIME_TYPES = {
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
    ".mp4": {"video/mp4"},
    ".avi": {"video/x-msvideo", "video/avi", "video/msvideo"},
    ".mov": {"video/quicktime"},
    ".mkv": {"video/x-matroska", "video/matroska"},
}


def _upload_error(message: str, status_code: int = 400):
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "message": message},
    )


def _get_upload_size_limit(suffix: str) -> int:
    if suffix in ALLOWED_IMAGE_EXTENSIONS:
        return IMAGE_MAX_UPLOAD_SIZE
    return VIDEO_MAX_UPLOAD_SIZE


def _validate_upload_filename(filename: str) -> tuple[str, str]:
    if not filename or not filename.strip():
        raise ValueError("Empty filename is not allowed")

    original_path = Path(filename)
    if original_path.is_absolute() or original_path.name != filename:
        raise ValueError("Invalid filename")

    suffix = original_path.suffix.lower()
    if suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValueError("Unsupported file type")

    return original_path.name, suffix


def _resolve_upload_target(upload_dir: Path, filename: str) -> Path:
    upload_root = upload_dir.resolve()
    target_path = (upload_dir / filename).resolve()
    target_path.relative_to(upload_root)
    return target_path


def _resolve_deletable_upload_path(upload_dir: Path, filename: str) -> Path:
    if not filename or not filename.strip():
        raise ValueError("Empty filename is not allowed")

    raw_path = Path(filename)
    if raw_path.is_absolute() or ".." in raw_path.parts:
        raise ValueError("Invalid file path")

    if raw_path.parts and raw_path.parts[0] == "uploads":
        raw_path = Path(*raw_path.parts[1:])

    if not raw_path.parts or len(raw_path.parts) != 1:
        raise ValueError("Invalid file path")

    return _resolve_upload_target(upload_dir, raw_path.name)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    saved_path = None
    try:
        # 确保上传目录存在
        upload_dir = settings.upload_dir
        upload_dir.mkdir(exist_ok=True)

        original_filename, suffix = _validate_upload_filename(file.filename or "")
        content_type = (file.content_type or "").lower()
        allowed_mime_types = ALLOWED_UPLOAD_MIME_TYPES.get(suffix, set())
        if content_type and content_type not in allowed_mime_types:
            return _upload_error("Unsupported file MIME type")

        safe_filename = f"{uuid.uuid4().hex}{suffix}"
        file_path = _resolve_upload_target(upload_dir, safe_filename)
        max_size = _get_upload_size_limit(suffix)

        total_size = 0
        saved_path = file_path
        
        # 保存文件（使用异步I/O）
        async with aiofiles.open(file_path, "wb") as f:
            while True:
                chunk = await file.read(UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break

                total_size += len(chunk)
                if total_size > max_size:
                    await f.close()
                    if file_path.exists():
                        file_path.unlink()
                    return _upload_error("Uploaded file is too large", status_code=413)

                await f.write(chunk)

        relative_file_path = f"uploads/{safe_filename}"
        return {
            "success": True,
            "file_path": relative_file_path,
            "filename": safe_filename,
            "original_filename": original_filename,
        }
    except ValueError as e:
        return _upload_error(str(e))
    except Exception as e:
        if saved_path and saved_path.exists():
            try:
                saved_path.unlink()
            except Exception:
                pass
        return {"success": False, "message": str(e)}
    finally:
        try:
            await file.close()
        except Exception:
            pass


@app.delete("/upload/{filename:path}")
async def delete_uploaded_file(filename: str):
    """删除已上传的文件"""
    try:
        upload_dir = settings.upload_dir
        file_path = _resolve_deletable_upload_path(upload_dir, filename)
        
        # 安全检查：确保文件路径在uploads目录内
        if not file_path.exists():
            return {"success": False, "message": "File not found"}
        if not file_path.is_file():
            return {"success": False, "message": "Invalid file path"}

        file_path.unlink()
        return {"success": True, "message": "File deleted successfully"}
    except ValueError as e:
        return {"success": False, "message": str(e)}
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
    if camera_config is not None and not isinstance(camera_config, dict):
        camera_config = dict(camera_config)
    
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
    """
    WebSocket 端点 - 多订阅者共享 pipeline 架构 + 后台/展示结果分离
    
    新架构流程：
    1. 根据 kind+value+camera_id 生成唯一的 source_key
    2. 从 session_manager 获取或创建 SourceSession
    3. 将当前 WebSocket 注册为该 session 的订阅者
    4. 等待 display_version 变化时发送已编码结果（避免重复编码和发送）
    5. 断开时自动取消订阅和释放资源
    
    关键优化：
    - 版本检查：只有当 display_version 变化时才发送
    - 统一编码：多订阅者共享已编码的 JPEG
    - 避免重复编码：每个新的展示帧只编码一次
    - 后台模式：无前端时不生成展示帧和编码
    """
    await ws.accept()
    await ws_manager.register(ws)

    print(f"{get_timestamp()} [WS] New connection: kind={kind}, value={value}, camera_id={camera_id}, pen_id={pen_id}, barn_id={barn_id}", 
          flush=True)

    session_mgr = get_session_manager()
    source_key = None
    session = None

    try:
        # 前端是 urlencode 过的,这里必须 decode
        if value is not None:
            value = unquote(value)
        print(f"{get_timestamp()} [WS] DECODED value = {value}", flush=True)

        # 生成唯一的 source key
        source_key = SourceKey(kind=kind, value=value, camera_id=camera_id)
        print(f"{get_timestamp()} [WS] Source key: {source_key}", flush=True)

        # 在线程池中创建 stream 和 detector（阻塞操作）
        loop = asyncio.get_event_loop()
        
        def _create_session():
            """在线程中创建或获取 session"""
            # 1. 创建流
            stream = open_source(kind, value or "")
            
            # 2. 设置元数据
            if camera_id:
                stream.camera_id = camera_id
            if pen_id:
                stream.pen_id = pen_id
            if barn_id:
                stream.barn_id = barn_id
            
            # 3. 为本 session 创建专属 detector
            detector = PTDetector(C.PT_MODEL_PATH)
            
            # 4. 从 session_manager 获取或创建 session
            # 这是关键：如果同源已有 session，就复用；否则创建新的
            return session_mgr.get_or_create_session(source_key, stream, detector)
        
        session = await loop.run_in_executor(None, _create_session)
        
        # 将当前 WebSocket 注册为该 session 的订阅者
        session.add_subscriber(ws)
        print(f"{get_timestamp()} [WS] Registered as subscriber, session: {source_key}", flush=True)

        # 接收 session 的广播结果并发送给客户端
        # 优化：版本检查机制，避免重复发送
        frame_count = 0
        last_sent_display_version = -1  # 记录上次发送的版本
        
        while True:
            try:
                # 获取当前 display_version
                current_display_version = session.get_display_version()
                
                # 版本未变化，不需要发送，等待新帧
                if current_display_version == last_sent_display_version:
                    await asyncio.sleep(0.01)
                    continue
                
                # 版本变化，有新的展示帧，进行发送
                # 注意：send_frame 会调用 session.encode_and_cache_jpeg() 进行统一编码
                try:
                    await ws_manager.send_frame(ws, None, session=session)
                    last_sent_display_version = current_display_version
                    
                    # 打印发送日志（每10帧打印一次）
                    frame_count += 1
                    if frame_count % 10 == 0:
                        ws_count = session.get_ws_subscriber_count()
                        print(f"{get_timestamp()} [SEND] source_key={source_key} ws_id={id(ws)} "
                              f"frame_id={frame_count} display_version={current_display_version} "
                              f"total_subscribers={ws_count}", flush=True)
                
                except RuntimeError as e:
                    # WebSocket 已断开
                    if "WebSocket send failed" in str(e):
                        break
                    raise
                
                # 短暂等待避免过快
                await asyncio.sleep(0.001)

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

        # 从 session 中注销该订阅者
        # session 如果引用计数为 0，会被后台清理线程在 TTL 后销毁
        if session and source_key:
            try:
                session.remove_subscriber(ws)
                print(f"{get_timestamp()} [WS] Unregistered from session: {source_key}, "
                      f"remaining_subscribers={session.get_ws_subscriber_count()}", flush=True)
            except Exception as e:
                print(f"{get_timestamp()} [WS] Error unregistering from session: {e}", flush=True)

        # 注销 WebSocket
        await ws_manager.unregister(ws)

        # 关闭 WebSocket 连接
        try:
            await ws.close()
        except Exception:
            pass

        print(f"{get_timestamp()} [WS] Cleanup complete", flush=True)
