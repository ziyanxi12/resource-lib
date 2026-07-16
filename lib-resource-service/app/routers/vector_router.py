"""
向量管理路由（包含搜索、补录、LLM API）

POST /api/vector/search        向量搜索（原版，返回完整字段）
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
from app.models.resource import Resource
from app.routers.resources import _fmt
from app.services.vector_sync_service import detect_missing_resources, sync_vectors_by_type

router = APIRouter(prefix="/api/vector", tags=["向量管理"])


class SearchRequest(BaseModel):
    type: str
    queries: List[str]
    mode: str = Field(default_factory=lambda: settings.VECTOR_SEARCH_MODE)
    top_k: int = 10
    filters: Optional[Dict[str, Any]] = None
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


def _enrich(raw_results: List[dict], db: Session, vec_type: str) -> List[dict]:
    """将向量服务返回的单组结果补充 DB 资源信息。"""
    data_ids = [r["data_id"] for r in raw_results if r.get("data_id") is not None]
    if not data_ids:
        return []

    resources_by_data_id = _lookup_resources(db, vec_type, data_ids)

    output = []
    for r in raw_results:
        data_id = r.get("data_id")
        res_row = resources_by_data_id.get(str(data_id)) if data_id is not None else None
        if res_row is None:
            continue
        item = _fmt(res_row)
        item["vector_text"] = r.get("text")
        item["score"] = r.get("score")
        output.append(item)
    return output


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
    """向量搜索 - 原版（返回完整字段）"""
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
            filters=req.filters or None,
            hybrid_weight=req.hybrid_weight,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"向量服务调用失败：{e}")

    results = [_enrich(group, db, vec_type) for group in batch_raw]
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