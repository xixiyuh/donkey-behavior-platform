from fastapi import APIRouter
from .barn import router as barn_router
from .pen import router as pen_router
from .camera import router as camera_router
from .event import router as event_router
from .camera_config import router as camera_config_router, register_start_detection_func as cc_register_start, register_stop_detection_func as cc_register_stop
from .routes import router as routes_router

# 全局路由器
router = APIRouter(prefix="/api", tags=["farm"])

# 注册所有子路由器
router.include_router(barn_router)
router.include_router(pen_router)
router.include_router(camera_router)
router.include_router(event_router)
router.include_router(camera_config_router)
router.include_router(routes_router)

# 定义启动和停止检测的函数（稍后会被注册）
def start_camera_detection(config):
    """启动摄像头检测"""
    pass

def stop_camera_detection(config_id):
    """停止摄像头检测"""
    pass

# 注册启动和停止检测的函数
def register_start_detection_func(func):
    """注册启动检测的函数"""
    global start_camera_detection
    start_camera_detection = func
    # 同时注册到camera_config模块
    cc_register_start(func)

def register_stop_detection_func(func):
    """注册停止检测的函数"""
    global stop_camera_detection
    stop_camera_detection = func
    # 同时注册到camera_config模块
    cc_register_stop(func)

# 导出路由器和注册函数
__all__ = ['router', 'register_start_detection_func', 'register_stop_detection_func', 'start_camera_detection', 'stop_camera_detection']
