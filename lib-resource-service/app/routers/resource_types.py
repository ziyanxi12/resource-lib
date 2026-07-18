"""
资源类型接口
GET /api/resource-types 获取所有资源类型定义
"""

from fastapi import APIRouter

from app.enums import ResourceType

router = APIRouter(prefix="/api/resource-types", tags=["资源类型"])


@router.get("")
def get_resource_types():
    """获取所有资源类型定义"""
    items = []
    for rt in ResourceType:
        items.append({
            "id": rt.value,
            "name": rt.name,
            "label": rt.label,
        })
    return {"items": items}