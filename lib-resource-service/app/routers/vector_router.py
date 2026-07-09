"""
向量管理路由（包含搜索、补录、LLM API）

POST /api/vector/search        向量搜索（原版，返回完整字段）
POST /api/vector/search/llm    LLM 精简版搜索（返回 data_id + vector_text + score）
GET  /api/vector/detail        通过 data_id + type 获取全量数据
GET  /api/vector/missing/{type} 检测缺失向量
POST /api/vector/sync          精准补录向量
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, selectinload

from app.clients import vector_client
from app.config import settings
from app.database import get_db
from app.enums import ResourceType
from app.models.resource import ComponentVariant, Resource, ResourceIcon, ResourceIllus
from app.routers.resources import _fmt, _build_vector_text
from app.services.vector_text_builder import get_registry
from app.services.vector_sync_service import detect_missing_data_ids, sync_missing_vectors, rebuild_all_vectors

router = APIRouter(prefix="/api/vector", tags=["向量管理"])


# ──────────────────────────────────────────────────────────────────
# 向量搜索基础功能（HEAD 版本）
# ──────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    type: str
    queries: List[str]
    mode: str = Field(default_factory=lambda: settings.VECTOR_SEARCH_MODE)
    top_k: int = 10
    filters: Optional[Dict[str, Any]] = None
    hybrid_weight: float = 0.7


def _resolve_vec_type(req_type: str) -> Optional[str]:
    """将前端传入的 type 字符串解析为向量服务集合名。"""
    try:
        rt = ResourceType[req_type]
        spec = get_registry().get(rt)
        if spec:
            return spec.vec_type
    except KeyError:
        pass
    all_vec_types = {spec.vec_type for spec in get_registry().values()}
    if req_type in all_vec_types:
        return req_type
    return None


_LOAD_OPTS = [
    selectinload(Resource.tags),
    selectinload(Resource.component_variant),
    selectinload(Resource.icon_detail),
    selectinload(Resource.illus_detail),
]


def _lookup_resources(db: Session, vec_type: str, data_ids: List[str]) -> Dict[str, Any]:
    """按 vec_type 用稳定业务 ID 反查 Resource，返回 {data_id: Resource}。"""
    if not data_ids:
        return {}

    if vec_type == "component":
        rows = db.query(Resource).join(
            ComponentVariant, ComponentVariant.resource_id == Resource.id
        ).options(*_LOAD_OPTS).filter(
            ComponentVariant.variant_key.in_(data_ids),
            Resource.is_deleted == 0,
        ).all()
        return {row.component_variant.variant_key: row for row in rows}

    if vec_type == "icon":
        rows = db.query(Resource).join(
            ResourceIcon, ResourceIcon.resource_id == Resource.id
        ).options(*_LOAD_OPTS).filter(
            ResourceIcon.icon_id.in_(data_ids),
            Resource.is_deleted == 0,
        ).all()
        return {row.icon_detail.icon_id: row for row in rows}

    if vec_type == "illus":
        rows = db.query(Resource).join(
            ResourceIllus, ResourceIllus.resource_id == Resource.id
        ).options(*_LOAD_OPTS).filter(
            ResourceIllus.illus_id.in_(data_ids),
            Resource.is_deleted == 0,
        ).all()
        return {row.illus_detail.illus_id: row for row in rows}

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
        item["score"] = r.get("score")
        output.append(item)
    return output


# ──────────────────────────────────────────────────────────────────
# LLM 精简版专用（新增）
# ──────────────────────────────────────────────────────────────────

def _get_data_id(r: Resource) -> str:
    """按资源类型返回向量库 data_id"""
    if r.resource_type == 1:
        return r.component_variant.variant_key if r.component_variant else str(r.id)
    elif r.resource_type == 3:
        return r.icon_detail.icon_id if r.icon_detail else str(r.id)
    elif r.resource_type == 4:
        return r.illus_detail.illus_id if r.illus_detail else str(r.id)
    else:
        return str(r.id)


def _fmt_llm(r: Resource) -> dict:
    """LLM 精简版：仅返回 data_id + vector_text"""
    return {
        "data_id": _get_data_id(r),
        "vector_text": _build_vector_text(r),
    }


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
            item = _fmt_llm(res_row)
            item["score"] = r.get("score")
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


# ──────────────────────────────────────────────────────────────────
# 向量搜索（原版，HEAD 版本）
# ──────────────────────────────────────────────────────────────────

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


# ──────────────────────────────────────────────────────────────────
# 向量补录（工作区版本）
# ──────────────────────────────────────────────────────────────────

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
        "missing_ids": ["f884...", "3c44...", ...]
    }
    """
    try:
        rt = ResourceType(resource_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"未知 resource_type: {resource_type}，可选值: {[e.value for e in ResourceType]}"
        )
    
    result = detect_missing_data_ids(db, rt)
    result["resource_type"] = rt.name
    return result


@router.post("/rebuild")
def rebuild_vectors(
    resource_type: int = Query(..., description="资源类型 ID：1=component 2=template 3=icon 4=illus 5=image"),
    batch_size: int = Query(200, ge=50, le=500, description="每批处理数量（50-500）"),
    db: Session = Depends(get_db),
):
    """
    全量重建向量库：从 DB 读取所有记录并入向量，适用于向量库清空后的完整恢复。

    示例：POST /api/vector/rebuild?resource_type=3

    返回：
    {
        "resource_type": "icon",
        "total": 800,
        "synced": 800,
        "batch_count": 4,
        "failed": []
    }
    """
    try:
        rt = ResourceType(resource_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"未知 resource_type: {resource_type}，可选值: {[e.value for e in ResourceType]}",
        )

    result = rebuild_all_vectors(db, rt, batch_size=batch_size)
    result["resource_type"] = rt.name
    return result


@router.post("/sync")
def sync_vectors(
    resource_type: int = Query(..., description="资源类型 ID：1=component 2=template 3=icon 4=illus 5=image"),
    batch_size: int = Query(200, ge=50, le=500, description="每批处理数量（50-500）"),
    dry_run: bool = Query(False, description="只检测不实际补录"),
    db: Session = Depends(get_db)
):
    """
    精准补录缺失的向量数据
    
    示例：POST /api/vector/sync?resource_type=1&batch_size=200
    
    返回：
    {
        "resource_type": "component",
        "detected_missing": 5,
        "actual_synced": 5,
        "batch_count": 1,
        "failed": [],
        "dry_run": false
    }
    
    工作流程：
    1. 检测数据库存在但向量库缺失的 data_id
    2. 反查数据库完整记录
    3. 构造向量文本和 metadata
    4. 分批调用向量服务进行补录
    """
    try:
        rt = ResourceType(resource_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"未知 resource_type: {resource_type}，可选值: {[e.value for e in ResourceType]}"
        )
    
    result = sync_missing_vectors(db, rt, batch_size=batch_size, dry_run=dry_run)
    result["resource_type"] = rt.name
    return result