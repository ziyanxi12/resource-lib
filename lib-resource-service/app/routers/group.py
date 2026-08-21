"""
分组管理路由
GET    /api/groups           获取分组树（按资源类型）
POST   /api/groups           新建分组
PUT    /api/groups/{id}      更新分组名称
DELETE /api/groups/{id}      删除分组
PUT    /api/groups/{id}/move 移动分组
PUT    /api/groups/reorder   批量重排序
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.enums import ResourceType
from app.routers.resources import _fmt
from app.services import group_service
from app.services import operation_log_service
from app.services.operator import get_operator
from app.services.user_service import resolve_display_names
from app.schemas.group import (
    GroupCreate, GroupUpdate, GroupMove,
    GroupReorderRequest, GroupTreeResponse
)

router = APIRouter(prefix="/api/groups", tags=["分组管理"])


@router.get("")
def get_groups(
    type: str = Query(..., description="资源类型名，如 component、icon、illus、image、file"),
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
def create_group(body: GroupCreate, request: Request, db: Session = Depends(get_db)):
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

    account, name = get_operator(request)
    operation_log_service.create_log(
        db,
        source_id=body.source_id,
        resource_type=int(resource_type),
        operator=name,
        operator_account=account,
        action="create",
        target_type="group",
        target_id=group.id,
        target_name=group.name,
    )

    return {
        "id": group.id,
        "name": group.name,
        "parent_id": group.parent_id,
        "source_id": group.source_id,
        "level": group.level,
        "real_path": group.real_path,
        "sort_order": group.sort_order,
    }


@router.get("/with-resources")
def get_groups_with_resources(
    type: str = Query(..., description="资源类型名，如 component、icon、illus、image、file"),
    source_id: Optional[int] = Query(None, description="来源ID筛选"),
    exclude_default: bool = Query(True, description="是否排除默认分组"),
    limit: int = Query(10, ge=1, le=50, description="每个分组返回的资源数"),
    db: Session = Depends(get_db),
):
    """获取分组树，每个分组附带随机采样的直属资源"""
    try:
        resource_type = ResourceType.from_name(type)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"未知资源类型: {type}")

    tree, resources_map, type_name = group_service.get_group_tree_with_resources(
        db, int(resource_type), source_id, exclude_default, limit
    )

    accounts = set()
    for resources in resources_map.values():
        for r in resources:
            if r.created_by:
                accounts.add(r.created_by)
            if r.updated_by:
                accounts.add(r.updated_by)
    display_map = resolve_display_names(db, list(accounts))

    def _node_to_dict(node):
        d = node.model_dump()
        d["resources"] = [_fmt(r, display_map) for r in resources_map.get(node.id, [])]
        d["children"] = [_node_to_dict(c) for c in node.children]
        return d

    items = [_node_to_dict(n) for n in tree]

    return {
        "resource_type": int(resource_type),
        "resource_type_name": type_name,
        "source_id": source_id,
        "items": items,
    }


@router.get("/{group_id}")
def get_group(group_id: int, db: Session = Depends(get_db)):
    """获取单个分组详情（用于按分组反查来源/类型，支持分组深链）"""
    group = group_service.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    return {
        "id": group.id,
        "name": group.name,
        "parent_id": group.parent_id,
        "source_id": group.source_id,
        "resource_type": group.resource_type,
        "level": group.level,
        "real_path": group.real_path,
        "sort_order": group.sort_order,
        "is_default": group.is_default,
    }


@router.put("/{group_id}")
def update_group(group_id: int, body: GroupUpdate, request: Request, db: Session = Depends(get_db)):
    if not body.name:
        raise HTTPException(status_code=400, detail="名称不能为空")

    group = group_service.update_group(db, group_id, body.name)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    account, name = get_operator(request)
    operation_log_service.create_log(
        db,
        source_id=group.source_id,
        resource_type=group.resource_type,
        operator=name,
        operator_account=account,
        action="update",
        target_type="group",
        target_id=group.id,
        target_name=group.name,
    )

    return {"id": group_id, "name": group.name}


@router.get("/{group_id}/resource-count")
def get_resource_count(group_id: int, db: Session = Depends(get_db)):
    count = group_service.get_descendants_resource_count(db, group_id)
    return {"count": count}


@router.delete("/{group_id}")
def delete_group(group_id: int, request: Request, db: Session = Depends(get_db)):
    group = group_service.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    g_name = group.name
    g_source_id = group.source_id
    g_type = group.resource_type

    try:
        ok = group_service.delete_group(db, group_id)
        if not ok:
            raise HTTPException(status_code=404, detail="分组不存在")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    account, name = get_operator(request)
    operation_log_service.create_log(
        db,
        source_id=g_source_id,
        resource_type=g_type,
        operator=name,
        operator_account=account,
        action="delete",
        target_type="group",
        target_id=group_id,
        target_name=g_name,
    )

    return {"id": group_id, "message": "删除成功"}


@router.put("/{group_id}/move")
def move_group(group_id: int, body: GroupMove, request: Request, db: Session = Depends(get_db)):
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

    account, name = get_operator(request)
    operation_log_service.create_log(
        db,
        source_id=group.source_id,
        resource_type=group.resource_type,
        operator=name,
        operator_account=account,
        action="move",
        target_type="group",
        target_id=group.id,
        target_name=group.name,
        detail={"parent_id": body.parent_id},
    )

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