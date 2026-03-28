from fastapi import APIRouter, HTTPException
from ..models import CameraConfig
from ..schemas import CameraConfig as CameraConfigSchema, CameraConfigCreate

# 延迟导入启动和停止检测的函数
start_camera_detection = None
stop_camera_detection = None

# 注册启动和停止检测的函数
def register_start_detection_func(func):
    global start_camera_detection
    start_camera_detection = func

def register_stop_detection_func(func):
    global stop_camera_detection
    stop_camera_detection = func

router = APIRouter(prefix="/camera-configs", tags=["camera-configs"])

@router.post("", response_model=CameraConfigSchema)
def create_camera_config(config: CameraConfigCreate):
    config_id = CameraConfig.create(
        config.camera_id, config.flv_url, config.barn_id, config.pen_id,
        config.start_time, config.end_time
    )
    created_config = CameraConfig.get_by_id(config_id)
    if not created_config:
        raise HTTPException(status_code=404, detail="Camera config not created")
    
    # 启动摄像头检测（新创建的配置默认是启用状态）
    if start_camera_detection:
        start_camera_detection(created_config)
    
    return {
        "id": created_config["id"],
        "camera_id": created_config["camera_id"],
        "flv_url": created_config["flv_url"],
        "barn_id": created_config["barn_id"],
        "pen_id": created_config["pen_id"],
        "start_time": created_config["start_time"],
        "end_time": created_config["end_time"],
        "enable": created_config["enable"],
        "created_at": created_config["created_at"]
    }

@router.get("")
def get_camera_configs(page: int = 1, page_size: int = 10):
    result = CameraConfig.get_all(page, page_size)
    return {
        "items": [{
            "id": config["id"],
            "camera_id": config["camera_id"],
            "flv_url": config["flv_url"],
            "barn_id": config["barn_id"],
            "pen_id": config["pen_id"],
            "start_time": config["start_time"],
            "end_time": config["end_time"],
            "enable": config["enable"],
            "created_at": config["created_at"]
        } for config in result['items']],
        "total": result['total'],
        "page": result['page'],
        "page_size": result['page_size']
    }

@router.patch("/{config_id}/toggle")
def toggle_camera_config(config_id: int):
    # 先获取当前状态
    current_config = CameraConfig.get_by_id(config_id)
    if not current_config:
        raise HTTPException(status_code=404, detail="Camera config not found")
    
    # 切换状态
    CameraConfig.toggle(config_id)
    
    # 获取切换后的状态
    updated_config = CameraConfig.get_by_id(config_id)
    if updated_config:
        if updated_config["enable"] == 1:
            # 如果切换后是启用状态，启动检测
            if start_camera_detection:
                start_camera_detection(updated_config)
        else:
            # 如果切换后是禁用状态，停止检测
            if stop_camera_detection:
                stop_camera_detection(config_id)
    
    return {"message": "Camera config toggled successfully"}

@router.delete("/{config_id}")
def delete_camera_config(config_id: int):
    CameraConfig.delete(config_id)
    return {"message": "Camera config deleted successfully"}
