"""
搜索应用管理路由
GET    /api/search-apps            列表
POST   /api/search-apps            创建（自动生成 app_id）
PUT    /api/search-apps/{id}       更新 name/remark
DELETE /api/search-apps/{id}       软删除
GET    /api/search-apps/export     导出全部 app 为 JSON
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.search_app import SearchAppCreate, SearchAppUpdate
from app.services import search_app_service

router = APIRouter(prefix="/api/search-apps", tags=["搜索应用"])


def _format_app(app) -> dict:
    return {
        "id": app.id,
        "app_id": app.app_id,
        "name": app.name,
        "remark": app.remark,
        "is_active": app.is_active,
        "created_at": int(app.created_at.timestamp() * 1000) if app.created_at else None,
        "updated_at": int(app.updated_at.timestamp() * 1000) if app.updated_at else None,
    }


@router.get("")
def list_apps(
    is_active: Optional[int] = Query(None, description="1=启用 0=禁用"),
    db: Session = Depends(get_db),
):
    apps = search_app_service.get_apps(db, is_active=is_active)
    return {"items": [_format_app(a) for a in apps]}


@router.get("/export")
def export_apps(db: Session = Depends(get_db)):
    """导出全部搜索应用为 JSON 数组（用于跨环境迁移）"""
    return search_app_service.export_apps(db)


@router.post("")
def create_app(body: SearchAppCreate, db: Session = Depends(get_db)):
    name = body.name
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="name is required")
    try:
        app = search_app_service.create_app(db, name=name.strip(), remark=body.remark)
        return _format_app(app)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{app_id_pk}")
def update_app(app_id_pk: int, body: SearchAppUpdate, db: Session = Depends(get_db)):
    app = search_app_service.update_app(db, app_id_pk, body.model_dump(exclude_unset=True))
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    return _format_app(app)


@router.delete("/{app_id_pk}")
def delete_app(app_id_pk: int, db: Session = Depends(get_db)):
    success = search_app_service.delete_app(db, app_id_pk)
    if not success:
        raise HTTPException(status_code=404, detail="应用不存在")
    return {"message": "已删除"}
