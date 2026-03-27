# backend/schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BarnBase(BaseModel):
    name: str
    total_pens: int

class BarnCreate(BarnBase):
    pass

class BarnUpdate(BarnBase):
    pass

class Barn(BarnBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PenBase(BaseModel):
    pen_number: int
    barn_id: int

class PenCreate(PenBase):
    pass

class PenUpdate(PenBase):
    pass

class Pen(PenBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class CameraBase(BaseModel):
    camera_id: str
    pen_id: int
    barn_id: int
    flv_url: str

class CameraCreate(CameraBase):
    pass

class CameraUpdate(CameraBase):
    pass

class Camera(CameraBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class MatingEventBase(BaseModel):
    camera_id: str
    pen_id: int
    barn_id: int
    start_time: datetime
    end_time: datetime
    duration: int
    avg_confidence: float
    max_confidence: float
    screenshot: Optional[str] = None

class MatingEventCreate(MatingEventBase):
    pass

class MatingEvent(MatingEventBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True