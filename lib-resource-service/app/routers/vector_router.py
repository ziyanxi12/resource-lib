from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, selectinload
from fastapi import Depends

from app.clients import vector_client
from app.config import settings
from app.database import get_db
from app.enums import ResourceType
from app.models.resource import ComponentVariant, Resource, ResourceIcon, ResourceIllus
from app.routers.resources import _fmt
from app.services.vector_text_builder import get_registry

router = APIRouter(prefix="/api/vector", tags=["向量搜索"])


class SearchRequest(BaseModel):
    type: str
    queries: List[str]
    mode: str = Field(default_factory=lambda: settings.VECTOR_SEARCH_MODE)
    top_k: int = 10
    filters: Optional[Dict[str, Any]] = None
    hybrid_weight: float = 0.7


def _resolve_vec_type(req_type: str) -> Optional[str]:
    """将前端传入的 type 字符串解析为向量服务集合名。"""
    # 优先按 ResourceType 枚举名查 registry
    try:
        rt = ResourceType[req_type]
        spec = get_registry().get(rt)
        if spec:
            return spec.vec_type
    except KeyError:
        pass
    # 兼容直接传 vec_type 字符串（如 "component"、"icon"）
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

    # template / image：data_id 仍为 resource.id
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


@router.post("/search")
def vector_search(req: SearchRequest, db: Session = Depends(get_db)):
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
