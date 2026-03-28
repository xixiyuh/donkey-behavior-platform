from fastapi import APIRouter, HTTPException
from typing import List
from ..models import Pen, Camera
from ..schemas import Pen as PenSchema, Camera as CameraSchema

router = APIRouter(tags=["routes"])

# 获取指定养殖舍的所有栏
@router.get("/barns/{barn_id}/pens", response_model=List[PenSchema])
def get_pens_by_barn(barn_id: int):
    pens = Pen.get_by_barn(barn_id)
    return [{
        "id": pen["id"],
        "pen_number": pen["pen_number"],
        "barn_id": pen["barn_id"],
        "created_at": pen["created_at"]
    } for pen in pens]

# 获取指定栏的所有摄像头
@router.get("/pens/{pen_id}/cameras", response_model=List[CameraSchema])
def get_cameras_by_pen(pen_id: int):
    cameras = Camera.get_by_pen(pen_id)
    return [{
        "id": camera["id"],
        "camera_id": camera["camera_id"],
        "pen_id": camera["pen_id"],
        "barn_id": camera["barn_id"],
        "flv_url": camera["flv_url"],
        "created_at": camera["created_at"]
    } for camera in cameras]
