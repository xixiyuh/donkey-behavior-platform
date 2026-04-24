from fastapi import APIRouter, HTTPException
from ..models import MatingEvent, Camera
from ..schemas import MatingEvent as MatingEventSchema, MatingEventCreate

# Keep router prefix empty so we can expose both collection and nested routes
# under /api with consistent REST-style paths. 
router = APIRouter(tags=["events"])

@router.post("/mating-events", response_model=MatingEventSchema)
def create_mating_event(event: MatingEventCreate):
    event_id = MatingEvent.create(
        event.camera_id, event.pen_id, event.barn_id, event.start_time, event.end_time,       
        event.duration, event.avg_confidence, event.max_confidence, event.movement,
        event.screenshot
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
        "movement": created_event["movement"],
        "screenshot": created_event["screenshot"],
        "created_at": created_event["created_at"]
    }

@router.get("/mating-events")
def get_mating_events(page: int = 1, page_size: int = 10):
    result = MatingEvent.get_all(page, page_size)
    return {
        "items": [{
            "id": event["id"],
            "camera_id": event["camera_id"],   
            "pen_id": event["pen_id"],
            "barn_id": event["barn_id"],       
            "start_time": event["start_time"], 
            "end_time": event["end_time"],     
            "duration": event["duration"],     
            "avg_confidence": event["avg_confidence"],
            "max_confidence": event["max_confidence"],
            "screenshot": event["screenshot"], 
            "created_at": event["created_at"]  
        } for event in result["items"]],       
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"]       
    }

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
        "screenshot": event["screenshot"],     
        "created_at": event["created_at"]      
    }

@router.get("/pens/{pen_id}/mating-events")    
def get_mating_events_by_pen(pen_id: int, page: int = 1, page_size: int = 10):
    result = MatingEvent.get_by_pen(pen_id, page, page_size)
    return {
        "items": [{
            "id": event["id"],
            "camera_id": event["camera_id"],   
            "pen_id": event["pen_id"],
            "barn_id": event["barn_id"],       
            "start_time": event["start_time"], 
            "end_time": event["end_time"],     
            "duration": event["duration"],     
            "avg_confidence": event["avg_confidence"],
            "max_confidence": event["max_confidence"],
            "screenshot": event["screenshot"], 
            "created_at": event["created_at"]  
        } for event in result["items"]],       
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"]       
    }

@router.get("/barns/{barn_id}/mating-events")  
def get_mating_events_by_barn(barn_id: int, page: int = 1, page_size: int = 10):
    result = MatingEvent.get_by_barn(barn_id, page, page_size)
    return {
        "items": [{
            "id": event["id"],
            "camera_id": event["camera_id"],   
            "pen_id": event["pen_id"],
            "barn_id": event["barn_id"],       
            "start_time": event["start_time"], 
            "end_time": event["end_time"],     
            "duration": event["duration"],     
            "avg_confidence": event["avg_confidence"],
            "max_confidence": event["max_confidence"],
            "screenshot": event["screenshot"], 
            "created_at": event["created_at"]  
        } for event in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"]       
    }

@router.get("/cameras/{camera_id}/mating-events")
def get_mating_events_by_camera(camera_id: int, page: int = 1, page_size: int = 10):
    camera = Camera.get_by_id(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    result = MatingEvent.get_by_camera(camera["camera_id"], page, page_size)
    return {
        "items": [{
            "id": event["id"],
            "camera_id": event["camera_id"],   
            "pen_id": event["pen_id"],
            "barn_id": event["barn_id"],       
            "start_time": event["start_time"], 
            "end_time": event["end_time"],     
            "duration": event["duration"],     
            "avg_confidence": event["avg_confidence"],
            "max_confidence": event["max_confidence"],
            "screenshot": event["screenshot"],
            "created_at": event["created_at"]  
        } for event in result["items"]],       
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"]       
    }
