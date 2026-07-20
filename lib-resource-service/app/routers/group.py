"""
分组管理路由
GET    /api/groups           获取分组树（按资源类型）
POST   /api/groups           新建分组
PUT    /api/groups/{id}      更新分组名称
DELETE /api/groups/{id}      删除分组
PUT    /api/groups/{id}/move 移动分组
PUT    /api/groups/reorder   批量重排序
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.enums import ResourceType
from app.services import group_service
from app.schemas.group import (
    GroupCreate, GroupUpdate, GroupMove,
    GroupReorderRequest, GroupTreeResponse
)

router = APIRouter(prefix="/api/groups", tags=["分组管理"])


@router.get("")
def get_groups(
    type: str = Query(..., description="资源类型名，如 component、template、icon、illus、image、file"),
    source_id: Optional[int] = Query(None, description="来源ID筛选"),
    exclude_default: bool = Query(True, description="是否排除默认分组"),
    db: Session = Depends(get_db),
):
    try:
        resource_type = ResourceType.from_name(type)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"未知资源类型: {type}")

    tree, type_name = group_service.get_group_tree(db, int(resource_type), source_id, exclude_default)
    return GroupTreeResponse(
        resource_type=int(resource_type),
        resource_type_name=type_name,
        source_id=source_id,
        items=tree
    )


@router.post("")
def create_group(body: GroupCreate, db: Session = Depends(get_db)):
    try:
        resource_type = ResourceType.from_name(body.type)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"未知资源类型: {body.type}")

    try:
        group = group_service.create_group(
            db,
            resource_type=int(resource_type),
            source_id=body.source_id,
            name=body.name,
            parent_id=body.parent_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "id": group.id,
        "name": group.name,
        "parent_id": group.parent_id,
        "source_id": group.source_id,
        "level": group.level,
        "real_path": group.real_path,
        "sort_order": group.sort_order,
    }


@router.put("/{group_id}")
def update_group(group_id: int, body: GroupUpdate, db: Session = Depends(get_db)):
    if not body.name:
        raise HTTPException(status_code=400, detail="名称不能为空")

    group = group_service.update_group(db, group_id, body.name)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    return {"id": group_id, "name": group.name}


@router.get("/{group_id}/resource-count")
def get_resource_count(group_id: int, db: Session = Depends(get_db)):
    count = group_service.get_descendants_resource_count(db, group_id)
    return {"count": count}


@router.delete("/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    try:
        ok = group_service.delete_group(db, group_id)
        if not ok:
            raise HTTPException(status_code=404, detail="分组不存在")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": group_id, "message": "删除成功"}


@router.put("/{group_id}/move")
def move_group(group_id: int, body: GroupMove, db: Session = Depends(get_db)):
    try:
        group = group_service.move_group(
            db,
            group_id,
            body.parent_id,
            body.sort_order
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    return {
        "id": group_id,
        "parent_id": group.parent_id,
        "level": group.level,
        "real_path": group.real_path,
        "sort_order": group.sort_order,
    }


@router.put("/reorder")
def reorder_groups(body: GroupReorderRequest, db: Session = Depends(get_db)):
    ok = group_service.reorder_groups(db, body.items)
    return {"message": "排序成功"}