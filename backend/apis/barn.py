from fastapi import APIRouter, HTTPException
import pymysql
from ..models import Barn
from ..schemas import Barn as BarnSchema, BarnCreate, BarnUpdate

router = APIRouter(prefix="/barns", tags=["barns"])

@router.post("", response_model=BarnSchema)
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
    except pymysql.IntegrityError as e:
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=400, detail=f"养殖舍名称 '{barn.name}' 已存在")
        raise HTTPException(status_code=400, detail="创建养殖舍失败")

@router.get("")
def get_barns(page: int = 1, page_size: int = 10):
    result = Barn.get_all(page, page_size)
    return {
        "items": [{
            "id": barn["id"],
            "name": barn["name"],
            "total_pens": barn["total_pens"],
            "created_at": barn["created_at"]
        } for barn in result['items']],
        "total": result['total'],
        "page": result['page'],
        "page_size": result['page_size']
    }

@router.get("/{barn_id}", response_model=BarnSchema)
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

@router.put("/{barn_id}", response_model=BarnSchema)
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

@router.delete("/{barn_id}")
def delete_barn(barn_id: int):
    existing_barn = Barn.get_by_id(barn_id)
    if not existing_barn:
        raise HTTPException(status_code=404, detail="Barn not found")
    Barn.delete(barn_id)
    return {"message": "Barn deleted successfully"}
