from fastapi import APIRouter, HTTPException, Path, Query
from typing import List
from ..models import Pen
from ..schemas import Pen as PenSchema, PenCreate, PenUpdate

router = APIRouter(prefix="/pens", tags=["pens"])

@router.post("", response_model=PenSchema)
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

@router.get("")
def get_pens(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100)):
    result = Pen.get_all(page, page_size)
    return {
        "items": [{
            "id": pen["id"],
            "pen_number": pen["pen_number"],
            "barn_id": pen["barn_id"],
            "created_at": pen["created_at"]
        } for pen in result['items']],
        "total": result['total'],
        "page": result['page'],
        "page_size": result['page_size']
    }

@router.get("/{pen_id}", response_model=PenSchema)
def get_pen(pen_id: int = Path(..., ge=1)):
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
def get_pens_by_barn(barn_id: int = Path(..., ge=1)):
    pens = Pen.get_by_barn(barn_id)
    return [{
        "id": pen["id"],
        "pen_number": pen["pen_number"],
        "barn_id": pen["barn_id"],
        "created_at": pen["created_at"]
    } for pen in pens]

@router.put("/{pen_id}", response_model=PenSchema)
def update_pen(pen: PenUpdate, pen_id: int = Path(..., ge=1)):
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

@router.delete("/{pen_id}")
def delete_pen(pen_id: int = Path(..., ge=1)):
    existing_pen = Pen.get_by_id(pen_id)
    if not existing_pen:
        raise HTTPException(status_code=404, detail="Pen not found")
    Pen.delete(pen_id)
    return {"message": "Pen deleted successfully"}
