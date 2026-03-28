from fastapi import APIRouter
from .barn import router as barn_router
from .pen import router as pen_router
from .camera import router as camera_router
from .event import router as event_router
from .camera_config import router as camera_config_router

# 全局路由器
router = APIRouter(prefix="/api", tags=["farm"])

# 注册所有子路由器
router.include_router(barn_router)
router.include_router(pen_router)
router.include_router(camera_router)
router.include_router(event_router)
router.include_router(camera_config_router)

# 导出路由器
__all__ = ['router']
