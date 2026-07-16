"""
向量搜索路由
实现三种响应模式：basic、normal、complete
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.enums import ResourceType
from app.models.resource import Resource

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resources", tags=["向量搜索"])


class SearchRequest(BaseModel):
    text: str = Field(..., description="搜索文本")
    resource_type: int = Field(..., description="资源类型（1-6）")
    source_id: Optional[int] = Field(None, description="来源ID筛选")
    group_id: Optional[int] = Field(None, description="分组ID筛选")
    top_k: int = Field(10, ge=1, le=50, description="返回最相似的K条结果")
    response_mode: str = Field("basic", description="响应模式：basic/normal/complete")


def _build_basic_response(resource: Resource, score: float) -> dict:
    """basic 模式：id, text, score"""
    return {
        "id": resource.id,
        "text": resource.vector_text or "",
        "score": score,
    }


def _build_normal_response(resource: Resource, score: float) -> dict:
    """normal 模式：id, text, score, raw_data"""
    return {
        "id": resource.id,
        "text": resource.vector_text or "",
        "score": score,
        "raw_data": resource.raw_data,
    }


def _build_complete_response(resource: Resource, score: float) -> dict:
    """complete 模式：全量数据"""
    return {
        "id": resource.id,
        "text": resource.vector_text or "",
        "score": score,
        "name": resource.name,
        "description": resource.description,
        "tags": [t.tag for t in resource.tags],
        "search_text": resource.search_text,
        "file_name": resource.file_name,
        "file_url": resource.file_url,
        "file_path": resource.file_path,
        "file_size": resource.file_size,
        "file_type": resource.file_type,
        "width": resource.width,
        "height": resource.height,
        "thumbnail_path": resource.thumbnail_path,
        "raw_data": resource.raw_data,
        "resource_type": resource.resource_type,
        "source_id": resource.source_id,
        "group_id": resource.group_id,
        "created_at": resource.created_at.isoformat() if resource.created_at else None,
        "updated_at": resource.updated_at.isoformat() if resource.updated_at else None,
    }


@router.post("/search")
def search_resources(request: SearchRequest, db: Session = Depends(get_db)):
    """
    向量搜索接口
    
    三种响应模式：
    - basic: 返回 id, text, score（LLM 专用）
    - normal: 返回 id, text, score, raw_data（外部系统调用）
    - complete: 返回全量数据（前端展示）
    """
    try:
        ResourceType(request.resource_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的 resource_type: {request.resource_type}")
    
    if request.response_mode not in ["basic", "normal", "complete"]:
        raise HTTPException(status_code=400, detail=f"无效的 response_mode: {request.response_mode}")
    
    if not settings.VECTOR_SERVICE_ENABLED:
        raise HTTPException(status_code=503, detail="向量服务未启用")
    
    try:
        from app.clients import vector_client
        from app.enums import ResourceType
        
        vec_type_map = {
            ResourceType.component: "component",
            ResourceType.template: "template",
            ResourceType.icon: "icon",
            ResourceType.illus: "illustration",
            ResourceType.image: "image",
            ResourceType.file: "file",
        }
        
        resource_type_enum = ResourceType(request.resource_type)
        vec_type = vec_type_map.get(resource_type_enum)
        
        if not vec_type:
            raise HTTPException(status_code=400, detail=f"不支持的资源类型: {request.resource_type}")
        
        filter_dict = {}
        if request.source_id is not None:
            filter_dict["source_id"] = request.source_id
        if request.group_id is not None:
            filter_dict["group_id"] = request.group_id
        
        results = vector_client.search(
            vec_type=vec_type,
            query_text=request.text,
            top_k=request.top_k,
            filter_dict=filter_dict if filter_dict else None,
        )
        
        if not results:
            return {"data": []}
        
        resource_ids = [int(r["id"]) for r in results]
        resources_map = {
            r.id: r
            for r in db.query(Resource).filter(Resource.id.in_(resource_ids)).all()
        }
        
        response_builder = {
            "basic": _build_basic_response,
            "normal": _build_normal_response,
            "complete": _build_complete_response,
        }[request.response_mode]
        
        data = []
        for result in results:
            resource_id = int(result["id"])
            resource = resources_map.get(resource_id)
            if resource:
                data.append(response_builder(resource, result.get("score", 0.0)))
        
        return {"data": data}
    
    except Exception as e:
        logger.exception("向量搜索失败")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")