"""
来源管理路由
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import source_service
from app.enums import ResourceType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sources", tags=["来源管理"])


@router.get("")
def list_sources(
    type: Optional[str] = Query(None, description="资源类型名，如 component、icon、illus"),
    is_active: Optional[int] = Query(None, description="是否启用筛选"),
    db: Session = Depends(get_db),
):
    """获取来源列表"""
    resource_type_int = None
    if type:
        try:
            resource_type_int = int(ResourceType.from_name(type))
        except KeyError:
            raise HTTPException(status_code=400, detail=f"未知资源类型: {type}")
    
    sources = source_service.get_sources(db, resource_type=resource_type_int, is_active=is_active)
    return {
        "items": [
            {
                "id": s.id,
                "name": s.name,
                "resource_type": s.resource_type,
                "is_sync_source": s.is_sync_source,
                "config": s.config,
                "is_active": s.is_active,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
            }
            for s in sources
        ]
    }


@router.get("/{source_id}")
def get_source(source_id: int, db: Session = Depends(get_db)):
    """获取来源详情"""
    source = source_service.get_source_by_id(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="来源不存在")
    return {
        "id": source.id,
        "name": source.name,
        "resource_type": source.resource_type,
        "is_sync_source": source.is_sync_source,
        "config": source.config,
        "is_active": source.is_active,
        "created_at": source.created_at.isoformat(),
        "updated_at": source.updated_at.isoformat(),
    }


@router.post("")
def create_source(data: dict, db: Session = Depends(get_db)):
    """创建来源"""
    if "type" not in data:
        raise HTTPException(status_code=400, detail="type is required")
    
    try:
        resource_type = ResourceType.from_name(data["type"])
    except KeyError:
        raise HTTPException(status_code=400, detail=f"未知资源类型: {data['type']}")
    
    create_data = {
        "name": data.get("name"),
        "resource_type": int(resource_type),
        "is_sync_source": data.get("is_sync_source", 0),
        "config": data.get("config"),
        "is_active": data.get("is_active", 1),
    }
    
    try:
        source = source_service.create_source(db, create_data)
        return {
            "id": source.id,
            "name": source.name,
            "resource_type": source.resource_type,
            "is_sync_source": source.is_sync_source,
            "config": source.config,
            "is_active": source.is_active,
            "created_at": source.created_at.isoformat(),
            "updated_at": source.updated_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{source_id}")
def update_source(source_id: int, data: dict, db: Session = Depends(get_db)):
    """更新来源"""
    try:
        source = source_service.update_source(db, source_id, data)
        if not source:
            raise HTTPException(status_code=404, detail="来源不存在")
        return {
            "id": source.id,
            "name": source.name,
            "resource_type": source.resource_type,
            "is_sync_source": source.is_sync_source,
            "config": source.config,
            "is_active": source.is_active,
            "created_at": source.created_at.isoformat(),
            "updated_at": source.updated_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    """删除来源"""
    success = source_service.delete_source(db, source_id)
    if not success:
        raise HTTPException(status_code=404, detail="来源不存在")
    return {"message": "删除成功"}