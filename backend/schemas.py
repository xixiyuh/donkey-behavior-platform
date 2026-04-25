# backend/schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import Annotated, Literal, Optional
from datetime import datetime
import re

CAMERA_ID_PATTERN = r"^[A-Za-z0-9_-]{1,50}$"
SUPPORTED_STREAM_SCHEMES = ("http://", "https://", "rtsp://", "rtmp://", "flv://", "hls://")
TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")

PositiveId = Annotated[int, Field(ge=1)]
PageNumber = Annotated[int, Field(ge=1)]
PageSize = Annotated[int, Field(ge=1, le=100)]
CameraIdStr = Annotated[str, Field(min_length=1, max_length=50, pattern=CAMERA_ID_PATTERN)]
NameStr = Annotated[str, Field(min_length=1, max_length=100)]
StreamUrlStr = Annotated[str, Field(min_length=1, max_length=500)]
TimeStr = Annotated[str, Field(min_length=5, max_length=5)]

class BarnBase(BaseModel):
    name: NameStr
    total_pens: Annotated[int, Field(ge=1, le=10000)]

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
    pen_number: Annotated[int, Field(ge=1, le=10000)]
    barn_id: PositiveId

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
    camera_id: CameraIdStr
    pen_id: PositiveId
    barn_id: PositiveId
    flv_url: StreamUrlStr

class CameraCreate(CameraBase):
    @field_validator("flv_url")
    @classmethod
    def validate_stream_url(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped.lower().startswith(SUPPORTED_STREAM_SCHEMES):
            raise ValueError("flv_url must start with http://, https://, rtsp://, rtmp://, flv://, or hls://")
        return stripped

class CameraUpdate(BaseModel):
    camera_id: Optional[CameraIdStr] = None
    pen_id: Optional[PositiveId] = None
    barn_id: Optional[PositiveId] = None
    flv_url: Optional[StreamUrlStr] = None

    @field_validator("flv_url")
    @classmethod
    def validate_stream_url(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped.lower().startswith(SUPPORTED_STREAM_SCHEMES):
            raise ValueError("flv_url must start with http://, https://, rtsp://, rtmp://, flv://, or hls://")
        return stripped

class Camera(CameraBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class MatingEventBase(BaseModel):
    camera_id: CameraIdStr
    pen_id: PositiveId
    barn_id: PositiveId
    start_time: datetime
    end_time: datetime
    duration: Annotated[int, Field(ge=0, le=86400)]
    avg_confidence: Annotated[float, Field(ge=0, le=1)]
    max_confidence: Annotated[float, Field(ge=0, le=1)]
    movement: Annotated[float, Field(ge=0)]
    screenshot: Optional[Annotated[str, Field(max_length=500)]] = None

class MatingEventCreate(MatingEventBase):
    pass

class MatingEvent(MatingEventBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class CameraConfigBase(BaseModel):
    camera_id: CameraIdStr
    flv_url: StreamUrlStr
    barn_id: PositiveId
    pen_id: PositiveId
    start_time: TimeStr = '09:00'
    end_time: TimeStr = '19:00'
    status: Literal[0, 1, 2] = 1
    enable: Literal[0, 1] = 1

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_value(cls, value: str) -> str:
        if not TIME_PATTERN.match(value):
            raise ValueError("time must use HH:MM format")
        hour, minute = value.split(":")
        if int(hour) > 23 or int(minute) > 59:
            raise ValueError("time must use HH:MM format")
        return value

class CameraConfigCreate(CameraConfigBase):
    @field_validator("flv_url")
    @classmethod
    def validate_stream_url(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped.lower().startswith(SUPPORTED_STREAM_SCHEMES):
            raise ValueError("flv_url must start with http://, https://, rtsp://, rtmp://, flv://, or hls://")
        return stripped

class CameraConfigEnableUpdate(BaseModel):
    enable: Literal[0, 1]

class CameraConfigStatusUpdate(BaseModel):
    status: Literal[0, 1, 2]

class CameraConfig(CameraConfigBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
