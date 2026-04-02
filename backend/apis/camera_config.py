from fastapi import APIRouter, HTTPException, Body
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
        config.start_time, config.end_time, config.status
    )
    created_config = CameraConfig.get_by_id(config_id)
    if not created_config:
        raise HTTPException(status_code=404, detail="Camera config not created")
    
    # 启动摄像头检测（如果状态是启用或自动且当前时间在范围内）
    if start_camera_detection:
        # 检查是否应该激活
        from datetime import datetime
        current_time = datetime.now().time()
        status = created_config["status"]
        
        if status == 1:  # 启用状态
            start_camera_detection(created_config)
        elif status == 2:  # 自动状态
            start_time = datetime.strptime(created_config['start_time'], '%H:%M').time()
            end_time = datetime.strptime(created_config['end_time'], '%H:%M').time()
            if start_time <= current_time <= end_time:
                start_camera_detection(created_config)
    
    return {
        "id": created_config["id"],
        "camera_id": created_config["camera_id"],
        "flv_url": created_config["flv_url"],
        "barn_id": created_config["barn_id"],
        "pen_id": created_config["pen_id"],
        "start_time": created_config["start_time"],
        "end_time": created_config["end_time"],
        "status": created_config["status"],
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
            "status": config["status"],
            "created_at": config["created_at"]
        } for config in result['items']],
        "total": result['total'],
        "page": result['page'],
        "page_size": result['page_size']
    }

@router.patch("/{config_id}/status")
def set_camera_config_status(config_id: int, status_data: dict = Body(...)):
    # 验证状态值
    status = status_data.get("status")
    if status not in [0, 1, 2]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be 0 (disabled), 1 (enabled), or 2 (auto)")
    
    # 先获取当前配置
    current_config = CameraConfig.get_by_id(config_id)
    if not current_config:
        raise HTTPException(status_code=404, detail="Camera config not found")
    
    # 设置状态
    CameraConfig.set_status(config_id, status)
    
    # 获取更新后的配置
    updated_config = CameraConfig.get_by_id(config_id)
    if updated_config:
        if status == 1:  # 启用状态，启动检测
            if start_camera_detection:
                start_camera_detection(updated_config)
        elif status == 0:  # 禁用状态，停止检测
            if stop_camera_detection:
                stop_camera_detection(config_id)
        elif status == 2:  # 自动状态，根据时间判断
            from datetime import datetime
            current_time = datetime.now().time()
            start_time = datetime.strptime(updated_config['start_time'], '%H:%M').time()
            end_time = datetime.strptime(updated_config['end_time'], '%H:%M').time()
            if start_time <= current_time <= end_time:
                if start_camera_detection:
                    start_camera_detection(updated_config)
            else:
                if stop_camera_detection:
                    stop_camera_detection(config_id)
    
    return {"message": "Camera config status updated successfully"}

@router.delete("/{config_id}")
def delete_camera_config(config_id: int):
    CameraConfig.delete(config_id)
    return {"message": "Camera config deleted successfully"}
