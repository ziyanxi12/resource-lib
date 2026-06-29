from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload, noload
from fastapi import Depends

from app.clients import vector_client
from app.database import get_db
from app.models.resource import Resource
from app.routers.resources import _fmt

router = APIRouter(prefix="/api/vector", tags=["向量搜索"])

_TYPE_MAP = {
    "component":     "component",
    "component_set": "component",
    "icon":          "icon",
    "svg":           "icon",
    "illustration":  "icon",
}


class SearchRequest(BaseModel):
    type: str
    query: str
    mode: str = "hybrid"
    top_k: int = 10
    filters: Optional[Dict[str, Any]] = None
    hybrid_weight: float = 0.7


@router.post("/search")
def vector_search(req: SearchRequest, db: Session = Depends(get_db)):
    vec_type = _TYPE_MAP.get(req.type)
    if vec_type is None:
        raise HTTPException(status_code=400, detail=f"不支持的 type：{req.type}")

    try:
        results = vector_client.search(
            vec_type=vec_type,
            query=req.query,
            mode=req.mode,
            top_k=req.top_k,
            filters=req.filters or None,
            hybrid_weight=req.hybrid_weight,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"向量服务调用失败：{e}")

    # 从 data_id（即 resource_id）批量查 DB 补充资源信息
    resource_ids = []
    for r in results:
        try:
            resource_ids.append(int(r["data_id"]))
        except (ValueError, KeyError):
            pass

    resources_by_id: dict[int, Resource] = {}
    if resource_ids:
        if vec_type == "component":
            eager = [
                selectinload(Resource.tags),
                selectinload(Resource.component_variant),
                noload(Resource.icon_detail),
            ]
        else:
            eager = [
                selectinload(Resource.tags),
                selectinload(Resource.icon_detail),
                noload(Resource.component_variant),
            ]
        rows = db.query(Resource).options(*eager).filter(
            Resource.id.in_(resource_ids),
            Resource.is_deleted == 0,
        ).all()
        resources_by_id = {row.id: row for row in rows}

    output = []
    for r in results:
        try:
            rid = int(r["data_id"])
        except (ValueError, KeyError):
            rid = None

        res_row = resources_by_id.get(rid) if rid else None
        if res_row is None:
            continue
        item = _fmt(res_row)
        item["score"] = r.get("score")
        output.append(item)

    return {"results": output}
