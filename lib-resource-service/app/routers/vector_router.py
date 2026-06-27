from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import Depends

from app.clients import vector_client
from app.database import get_db
from app.models.resource import Resource

router = APIRouter(prefix="/api/vector", tags=["向量搜索"])

_TYPE_MAP = {
    "component": "component",
    "icon": "icon",
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
        rows = db.query(Resource).filter(
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
        output.append({
            "data_id": r.get("data_id"),
            "score": r.get("score"),
            "text": r.get("text"),
            "metadata": r.get("metadata"),
            "resource": {
                "id": res_row.id,
                "name": res_row.name,
                "resource_type": res_row.resource_type,
                "description": res_row.description,
                "file_path": res_row.file_path,
                "thumbnail_path": res_row.thumbnail_path,
            } if res_row else None,
        })

    return {"results": output}
