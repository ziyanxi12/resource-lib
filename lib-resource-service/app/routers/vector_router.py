"""
向量管理路由（包含搜索、补录、LLM API）

POST /api/vector/search        向量搜索（支持批量、三种响应模式）
POST /api/vector/search/llm    LLM 精简版搜索（返回 data_id + vector_text + score）
GET  /api/vector/detail        通过 data_id + type 获取全量数据
GET  /api/vector/missing/{type} 检测缺失向量
POST /api/vector/rebuild       全量重建向量库
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, selectinload

from app.clients import vector_client
from app.config import settings
from app.database import get_db
from app.enums import ResourceType
from app.models.resource import Resource, ResourceGroup
from app.routers.resources import _fmt
from app.services.vector_sync_service import detect_missing_resources, sync_vectors_by_type

router = APIRouter(prefix="/api/vector", tags=["向量管理"])


def _get_all_group_ids_with_descendants(db: Session, group_id: int) -> List[int]:
    ids = [group_id]
    children = db.query(ResourceGroup).filter(ResourceGroup.parent_id == group_id).all()
    for child in children:
        ids.extend(_get_all_group_ids_with_descendants(db, child.id))
    return ids


class SearchRequest(BaseModel):
    type: str
    queries: List[str]
    mode: str = Field(default_factory=lambda: settings.VECTOR_SEARCH_MODE)
    top_k: int = 10
    filters: Optional[Dict[str, Any]] = None
    response_mode: str = Field(default="complete", description="响应模式：basic/normal/complete")
    hybrid_weight: float = 0.7


def _resolve_vec_type(req_type: str) -> Optional[str]:
    """将前端传入的 type 字符串解析为向量服务集合名。"""
    from app.enums import ResourceType as RT
    vec_type_map = {
        RT.component: "component",
        RT.template: "template",
        RT.icon: "icon",
        RT.illus: "illustration",
        RT.image: "image",
        RT.file: "file",
    }
    
    try:
        rt = ResourceType[req_type]
        return vec_type_map.get(rt)
    except KeyError:
        pass
    
    if req_type in vec_type_map.values():
        return req_type
    
    return None


_LOAD_OPTS = [
    selectinload(Resource.tags),
]


def _lookup_resources(db: Session, vec_type: str, data_ids: List[str]) -> Dict[str, Any]:
    """按 vec_type 用资源 ID 反查 Resource，返回 {data_id: Resource}。"""
    if not data_ids:
        return {}

    int_ids = [int(d) for d in data_ids if d.isdigit()]
    rows = db.query(Resource).options(*_LOAD_OPTS).filter(
        Resource.id.in_(int_ids),
        Resource.is_deleted == 0,
    ).all()
    return {str(row.id): row for row in rows}


def _enrich_llm(raw_results: List[dict], db: Session, vec_type: str) -> List[dict]:
    """LLM 版 enrichment，补充 score"""
    data_ids = [r["data_id"] for r in raw_results if r.get("data_id")]
    if not data_ids:
        return []
    
    resources_by_data_id = _lookup_resources(db, vec_type, data_ids)
    
    output = []
    for r in raw_results:
        data_id = r.get("data_id")
        res_row = resources_by_data_id.get(str(data_id)) if data_id else None
        if res_row:
            item = {
                "data_id": data_id,
                "vector_text": r.get("text"),
                "score": r.get("score"),
            }
            output.append(item)
    return output


def _build_basic_response(resource: Resource, raw_result: dict) -> dict:
    """basic 模式：id, vector_text, score"""
    return {
        "id": resource.id,
        "vector_text": raw_result.get("text", ""),
        "score": raw_result.get("score", 0.0),
    }


def _build_normal_response(resource: Resource, raw_result: dict) -> dict:
    """normal 模式：id, vector_text, score, raw_data"""
    return {
        "id": resource.id,
        "vector_text": raw_result.get("text", ""),
        "score": raw_result.get("score", 0.0),
        "raw_data": resource.raw_data,
    }


def _build_complete_response(resource: Resource, raw_result: dict) -> dict:
    """complete 模式：全量数据"""
    item = _fmt(resource)
    item["vector_text"] = raw_result.get("text")
    item["score"] = raw_result.get("score")
    return item


@router.post("/search/llm")
def vector_search_llm(req: SearchRequest, db: Session = Depends(get_db)):
    """向量搜索 - LLM 精简版（仅返回 data_id + vector_text + score）"""
    vec_type = _resolve_vec_type(req.type)
    if vec_type is None:
        raise HTTPException(status_code=400, detail=f"不支持的 type：{req.type}")
    if not req.queries:
        raise HTTPException(status_code=422, detail="queries 不能为空")
    
    try:
        batch_raw = vector_client.batch_search(
            vec_type=vec_type,
            queries=req.queries,
            mode=req.mode,
            top_k=req.top_k,
            filters=req.filters,
            hybrid_weight=req.hybrid_weight,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"向量服务调用失败：{e}")
    
    results = [_enrich_llm(group, db, vec_type) for group in batch_raw]
    return {"results": results}


@router.get("/detail")
def get_resource_by_data_id(
    type: str = Query(..., description="资源类型：component/icon/illus/template/image"),
    data_id: str = Query(..., description="向量库唯一标识"),
    db: Session = Depends(get_db),
):
    """通过 data_id + type 获取全量资源数据（完整字段）"""
    vec_type = _resolve_vec_type(type)
    if vec_type is None:
        raise HTTPException(status_code=400, detail=f"不支持的 type：{type}")
    
    resources_by_data_id = _lookup_resources(db, vec_type, [data_id])
    resource = resources_by_data_id.get(data_id)
    
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在或已删除")
    
    return _fmt(resource)


@router.post("/search")
def vector_search(req: SearchRequest, db: Session = Depends(get_db)):
    """
    向量搜索接口（支持批量、三种响应模式）
    
    参数说明：
    - type: 资源类型名（component/template/icon/illus/image/file）
    - queries: 批量搜索文本数组
    - mode: 搜索模式（hybrid/sparse/dense）
    - top_k: 每个 query 返回的数量
    - filters: 可选过滤条件（如 { source_id: 1, group_id: 2 }）
    - response_mode: 响应模式（basic/normal/complete）
    - hybrid_weight: 混合搜索权重
    
    响应模式：
    - basic: 返回 id, vector_text, score（LLM 专用）
    - normal: 返回 id, vector_text, score, raw_data（外部系统调用）
    - complete: 返回全量数据（前端展示，默认）
    """
    vec_type = _resolve_vec_type(req.type)
    if vec_type is None:
        raise HTTPException(status_code=400, detail=f"不支持的 type：{req.type}")
    
    if not req.queries:
        raise HTTPException(status_code=422, detail="queries 不能为空")
    
    if req.response_mode not in ["basic", "normal", "complete"]:
        raise HTTPException(status_code=400, detail=f"无效的 response_mode: {req.response_mode}，可选值: basic/normal/complete")

    filters = dict(req.filters) if req.filters else {}
    
    if "group_id" in filters:
        group_id = filters["group_id"]
        if isinstance(group_id, int):
            all_group_ids = _get_all_group_ids_with_descendants(db, group_id)
            filters["group_id"] = all_group_ids

    try:
        batch_raw = vector_client.batch_search(
            vec_type=vec_type,
            queries=req.queries,
            mode=req.mode,
            top_k=req.top_k,
            filters=filters if filters else None,
            hybrid_weight=req.hybrid_weight,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"向量服务调用失败：{e}")

    response_builder = {
        "basic": _build_basic_response,
        "normal": _build_normal_response,
        "complete": _build_complete_response,
    }[req.response_mode]

    results = []
    for group in batch_raw:
        data_ids = [r["data_id"] for r in group if r.get("data_id")]
        if not data_ids:
            results.append([])
            continue
        
        resources_by_data_id = _lookup_resources(db, vec_type, data_ids)
        
        group_results = []
        for r in group:
            data_id = r.get("data_id")
            res_row = resources_by_data_id.get(str(data_id)) if data_id else None
            if res_row:
                group_results.append(response_builder(res_row, r))
        
        results.append(group_results)

    return {"results": results}


@router.get("/missing/{resource_type}")
def get_missing(
    resource_type: int,
    db: Session = Depends(get_db)
):
    """
    检测指定资源类型的向量缺失情况
    
    示例：GET /api/vector/missing/1
    
    返回：
    {
        "resource_type": "component",
        "db_count": 4523,
        "vector_count": 4518,
        "missing_count": 5,
        "missing_ids": [1, 2, 3, ...]
    }
    """
    try:
        rt = ResourceType(resource_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"未知 resource_type: {resource_type}，可选值: {[e.value for e in ResourceType]}"
        )
    
    result = detect_missing_resources(db, rt)
    result["resource_type"] = rt.name
    return result


@router.post("/rebuild")
def rebuild_vectors(
    resource_type: int = Query(..., description="资源类型 ID：1=component 2=template 3=icon 4=illus 5=image"),
    db: Session = Depends(get_db),
):
    """
    全量重建向量库：触发时间戳同步

    示例：POST /api/vector/rebuild?resource_type=3

    返回：
    {
        "resource_type": "icon",
        "total": 800,
        "synced": 800,
        "failed": 0,
        "message": "同步完成：成功 800 条，失败 0 条"
    }
    """
    try:
        rt = ResourceType(resource_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"未知 resource_type: {resource_type}，可选值: {[e.value for e in ResourceType]}",
        )

    result = sync_vectors_by_type(db, rt)
    result["resource_type"] = rt.name
    return result


@router.post("/sync")
def sync_vectors(
    resource_type: int = Query(..., description="资源类型 ID：1=component 2=template 3=icon 4=illus 5=image"),
    db: Session = Depends(get_db)
):
    """
    精准补录缺失的向量数据（基于时间戳）
    
    示例：POST /api/vector/sync?resource_type=1
    
    返回：
    {
        "resource_type": "component",
        "total": 10,
        "synced": 10,
        "failed": 0,
        "message": "同步完成：成功 10 条，失败 0 条"
    }
    """
    try:
        rt = ResourceType(resource_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"未知 resource_type: {resource_type}，可选值: {[e.value for e in ResourceType]}"
        )
    
    result = sync_vectors_by_type(db, rt)
    result["resource_type"] = rt.name
    return result