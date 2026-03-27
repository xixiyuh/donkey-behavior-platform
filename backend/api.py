# backend/api.py
import sqlite3
from fastapi import APIRouter, HTTPException
from typing import List
from .models import Barn, Pen, Camera, MatingEvent
from .schemas import Barn as BarnSchema, BarnCreate, BarnUpdate
from .schemas import Pen as PenSchema, PenCreate, PenUpdate
from .schemas import Camera as CameraSchema, CameraCreate, CameraUpdate
from .schemas import MatingEvent as MatingEventSchema, MatingEventCreate

router = APIRouter(prefix="/api", tags=["farm"])

# 养殖舍相关API
@router.post("/barns", response_model=BarnSchema)
def create_barn(barn: BarnCreate):
    try:
        barn_id = Barn.create(barn.name, barn.total_pens)
        created_barn = Barn.get_by_id(barn_id)
        if not created_barn:
            raise HTTPException(status_code=404, detail="Barn not created")
        return {
            "id": created_barn["id"],
            "name": created_barn["name"],
            "total_pens": created_barn["total_pens"],
            "created_at": created_barn["created_at"]
        }
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail=f"养殖舍名称 '{barn.name}' 已存在")
        raise HTTPException(status_code=400, detail="创建养殖舍失败")

@router.get("/barns", response_model=List[BarnSchema])
def get_barns():
    barns = Barn.get_all()
    return [{
        "id": barn["id"],
        "name": barn["name"],
        "total_pens": barn["total_pens"],
        "created_at": barn["created_at"]
    } for barn in barns]

@router.get("/barns/{barn_id}", response_model=BarnSchema)
def get_barn(barn_id: int):
    barn = Barn.get_by_id(barn_id)
    if not barn:
        raise HTTPException(status_code=404, detail="Barn not found")
    return {
        "id": barn["id"],
        "name": barn["name"],
        "total_pens": barn["total_pens"],
        "created_at": barn["created_at"]
    }

@router.put("/barns/{barn_id}", response_model=BarnSchema)
def update_barn(barn_id: int, barn: BarnUpdate):
    existing_barn = Barn.get_by_id(barn_id)
    if not existing_barn:
        raise HTTPException(status_code=404, detail="Barn not found")
    Barn.update(barn_id, barn.name, barn.total_pens)
    updated_barn = Barn.get_by_id(barn_id)
    return {
        "id": updated_barn["id"],
        "name": updated_barn["name"],
        "total_pens": updated_barn["total_pens"],
        "created_at": updated_barn["created_at"]
    }

@router.delete("/barns/{barn_id}")
def delete_barn(barn_id: int):
    existing_barn = Barn.get_by_id(barn_id)
    if not existing_barn:
        raise HTTPException(status_code=404, detail="Barn not found")
    Barn.delete(barn_id)
    return {"message": "Barn deleted successfully"}

# 栏相关API
@router.post("/pens", response_model=PenSchema)
def create_pen(pen: PenCreate):
    pen_id = Pen.create(pen.pen_number, pen.barn_id)
    created_pen = Pen.get_by_id(pen_id)
    if not created_pen:
        raise HTTPException(status_code=404, detail="Pen not created")
    return {
        "id": created_pen["id"],
        "pen_number": created_pen["pen_number"],
        "barn_id": created_pen["barn_id"],
        "created_at": created_pen["created_at"]
    }

@router.get("/pens", response_model=List[PenSchema])
def get_pens():
    pens = Pen.get_all()
    return [{
        "id": pen["id"],
        "pen_number": pen["pen_number"],
        "barn_id": pen["barn_id"],
        "created_at": pen["created_at"]
    } for pen in pens]

@router.get("/pens/{pen_id}", response_model=PenSchema)
def get_pen(pen_id: int):
    pen = Pen.get_by_id(pen_id)
    if not pen:
        raise HTTPException(status_code=404, detail="Pen not found")
    return {
        "id": pen["id"],
        "pen_number": pen["pen_number"],
        "barn_id": pen["barn_id"],
        "created_at": pen["created_at"]
    }

@router.get("/barns/{barn_id}/pens", response_model=List[PenSchema])
def get_pens_by_barn(barn_id: int):
    pens = Pen.get_by_barn(barn_id)
    return [{
        "id": pen["id"],
        "pen_number": pen["pen_number"],
        "barn_id": pen["barn_id"],
        "created_at": pen["created_at"]
    } for pen in pens]

@router.put("/pens/{pen_id}", response_model=PenSchema)
def update_pen(pen_id: int, pen: PenUpdate):
    existing_pen = Pen.get_by_id(pen_id)
    if not existing_pen:
        raise HTTPException(status_code=404, detail="Pen not found")
    Pen.update(pen_id, pen.pen_number, pen.barn_id)
    updated_pen = Pen.get_by_id(pen_id)
    return {
        "id": updated_pen["id"],
        "pen_number": updated_pen["pen_number"],
        "barn_id": updated_pen["barn_id"],
        "created_at": updated_pen["created_at"]
    }

@router.delete("/pens/{pen_id}")
def delete_pen(pen_id: int):
    existing_pen = Pen.get_by_id(pen_id)
    if not existing_pen:
        raise HTTPException(status_code=404, detail="Pen not found")
    Pen.delete(pen_id)
    return {"message": "Pen deleted successfully"}

# 摄像头相关API
@router.post("/cameras", response_model=CameraSchema)
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

@router.get("/cameras", response_model=List[CameraSchema])
def get_cameras():
    cameras = Camera.get_all()
    return [{
        "id": camera["id"],
        "camera_id": camera["camera_id"],
        "pen_id": camera["pen_id"],
        "barn_id": camera["barn_id"],
        "flv_url": camera["flv_url"],
        "created_at": camera["created_at"]
    } for camera in cameras]

@router.get("/cameras/{camera_id}", response_model=CameraSchema)
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

@router.put("/cameras/{camera_id}", response_model=CameraSchema)
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

@router.delete("/cameras/{camera_id}")
def delete_camera(camera_id: int):
    existing_camera = Camera.get_by_id(camera_id)
    if not existing_camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    Camera.delete(camera_id)
    return {"message": "Camera deleted successfully"}

# Mating事件相关API
@router.post("/mating-events", response_model=MatingEventSchema)
def create_mating_event(event: MatingEventCreate):
    event_id = MatingEvent.create(
        event.camera_id, event.pen_id, event.barn_id, event.start_time, event.end_time, 
        event.duration, event.avg_confidence, event.max_confidence, 
        event.screenshot1, event.screenshot2, event.screenshot3
    )
    created_event = MatingEvent.get_by_id(event_id)
    if not created_event:
        raise HTTPException(status_code=404, detail="Mating event not created")
    return {
        "id": created_event["id"],
        "camera_id": created_event["camera_id"],
        "pen_id": created_event["pen_id"],
        "barn_id": created_event["barn_id"],
        "start_time": created_event["start_time"],
        "end_time": created_event["end_time"],
        "duration": created_event["duration"],
        "avg_confidence": created_event["avg_confidence"],
        "max_confidence": created_event["max_confidence"],
        "screenshot1": created_event["screenshot1"],
        "screenshot2": created_event["screenshot2"],
        "screenshot3": created_event["screenshot3"],
        "created_at": created_event["created_at"]
    }

@router.get("/mating-events", response_model=List[MatingEventSchema])
def get_mating_events():
    events = MatingEvent.get_all()
    return [{
        "id": event["id"],
        "camera_id": event["camera_id"],
        "pen_id": event["pen_id"],
        "barn_id": event["barn_id"],
        "start_time": event["start_time"],
        "end_time": event["end_time"],
        "duration": event["duration"],
        "avg_confidence": event["avg_confidence"],
        "max_confidence": event["max_confidence"],
        "screenshot1": event["screenshot1"],
        "screenshot2": event["screenshot2"],
        "screenshot3": event["screenshot3"],
        "created_at": event["created_at"]
    } for event in events]

@router.get("/mating-events/{event_id}", response_model=MatingEventSchema)
def get_mating_event(event_id: int):
    event = MatingEvent.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Mating event not found")
    return {
        "id": event["id"],
        "camera_id": event["camera_id"],
        "pen_id": event["pen_id"],
        "barn_id": event["barn_id"],
        "start_time": event["start_time"],
        "end_time": event["end_time"],
        "duration": event["duration"],
        "avg_confidence": event["avg_confidence"],
        "max_confidence": event["max_confidence"],
        "screenshot1": event["screenshot1"],
        "screenshot2": event["screenshot2"],
        "screenshot3": event["screenshot3"],
        "created_at": event["created_at"]
    }

@router.get("/pens/{pen_id}/mating-events", response_model=List[MatingEventSchema])
def get_mating_events_by_pen(pen_id: int):
    events = MatingEvent.get_by_pen(pen_id)
    return [{
        "id": event["id"],
        "camera_id": event["camera_id"],
        "pen_id": event["pen_id"],
        "barn_id": event["barn_id"],
        "start_time": event["start_time"],
        "end_time": event["end_time"],
        "duration": event["duration"],
        "avg_confidence": event["avg_confidence"],
        "max_confidence": event["max_confidence"],
        "screenshot1": event["screenshot1"],
        "screenshot2": event["screenshot2"],
        "screenshot3": event["screenshot3"],
        "created_at": event["created_at"]
    } for event in events]

@router.get("/barns/{barn_id}/mating-events", response_model=List[MatingEventSchema])
def get_mating_events_by_barn(barn_id: int):
    events = MatingEvent.get_by_barn(barn_id)
    return [{
        "id": event["id"],
        "camera_id": event["camera_id"],
        "pen_id": event["pen_id"],
        "barn_id": event["barn_id"],
        "start_time": event["start_time"],
        "end_time": event["end_time"],
        "duration": event["duration"],
        "avg_confidence": event["avg_confidence"],
        "max_confidence": event["max_confidence"],
        "screenshot1": event["screenshot1"],
        "screenshot2": event["screenshot2"],
        "screenshot3": event["screenshot3"],
        "created_at": event["created_at"]
    } for event in events]
