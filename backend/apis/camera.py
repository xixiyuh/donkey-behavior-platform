from fastapi import APIRouter, HTTPException
from typing import List
import sqlite3
from ..models import Camera
from ..schemas import Camera as CameraSchema, CameraCreate, CameraUpdate

router = APIRouter(prefix="/cameras", tags=["cameras"])

@router.post("", response_model=CameraSchema)
def create_camera(camera: CameraCreate):
    try:
        camera_id = Camera.create(camera.camera_id, camera.pen_id, camera.barn_id, camera.flv_url)
        created_camera = Camera.get_by_id(camera_id)
        if not created_camera:
            raise HTTPException(status_code=404, detail="Camera not created")
        return {
            "id": created_camera["id"],
            "camera_id": created_camera["camera_id"],
            "pen_id": created_camera["pen_id"],
            "barn_id": created_camera["barn_id"],
            "flv_url": created_camera["flv_url"],
            "created_at": created_camera["created_at"]
        }
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail=f"摄像头标识 '{camera.camera_id}' 已存在")
        raise HTTPException(status_code=400, detail="创建摄像头失败")

@router.get("")
def get_cameras(page: int = 1, page_size: int = 10):
    result = Camera.get_all(page, page_size)
    return {
        "items": [{
            "id": camera["id"],
            "camera_id": camera["camera_id"],
            "pen_id": camera["pen_id"],
            "barn_id": camera["barn_id"],
            "flv_url": camera["flv_url"],
            "created_at": camera["created_at"]
        } for camera in result['items']],
        "total": result['total'],
        "page": result['page'],
        "page_size": result['page_size']
    }

@router.get("/{camera_id}", response_model=CameraSchema)
def get_camera(camera_id: int):
    camera = Camera.get_by_id(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {
        "id": camera["id"],
        "camera_id": camera["camera_id"],
        "pen_id": camera["pen_id"],
        "barn_id": camera["barn_id"],
        "flv_url": camera["flv_url"],
        "created_at": camera["created_at"]
    }

@router.put("/{camera_id}", response_model=CameraSchema)
def update_camera(camera_id: int, camera: CameraUpdate):
    existing_camera = Camera.get_by_id(camera_id)
    if not existing_camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    Camera.update(camera_id, camera.camera_id, camera.pen_id, camera.barn_id, camera.flv_url)
    updated_camera = Camera.get_by_id(camera_id)
    return {
        "id": updated_camera["id"],
        "camera_id": updated_camera["camera_id"],
        "pen_id": updated_camera["pen_id"],
        "barn_id": updated_camera["barn_id"],
        "flv_url": updated_camera["flv_url"],
        "created_at": updated_camera["created_at"]
    }

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

@router.get("/barns/{barn_id}/cameras", response_model=List[CameraSchema])
def get_cameras_by_barn(barn_id: int):
    cameras = Camera.get_by_barn(barn_id)
    return [{
        "id": camera["id"],
        "camera_id": camera["camera_id"],
        "pen_id": camera["pen_id"],
        "barn_id": camera["barn_id"],
        "flv_url": camera["flv_url"],
        "created_at": camera["created_at"]
    } for camera in cameras]

@router.delete("/{camera_id}")
def delete_camera(camera_id: int):
    existing_camera = Camera.get_by_id(camera_id)
    if not existing_camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    Camera.delete(camera_id)
    return {"message": "Camera deleted successfully"}
