"""
向量服务 HTTP 客户端

封装对 Vector Management Service 的调用：
  - ingest：批量写入向量库
  - search：语义/全文/混合搜索
"""

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_BATCH_SIZE = 100


def ingest(vec_type: str, items: List[dict]) -> dict:
    """
    批量写入向量库，自动分批（每批 _BATCH_SIZE 条）。
    items 每条：{ data_id, text, metadata }
    返回汇总后的 { succeeded: [...], failed: [...] }
    """
    if not items:
        return {"succeeded": [], "failed": []}

    succeeded, failed = [], []
    for i in range(0, len(items), _BATCH_SIZE):
        batch = items[i: i + _BATCH_SIZE]
        try:
            resp = httpx.post(
                f"{settings.VECTOR_SERVICE_URL}/api/v1/ingest",
                json={"type": vec_type, "items": batch},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            succeeded.extend(data.get("succeeded", []))
            failed.extend(data.get("failed", []))
        except Exception as e:
            logger.warning("向量入库失败 (batch %d): %s", i // _BATCH_SIZE, e)
            failed.extend([{"data_id": it["data_id"], "error": str(e)} for it in batch])

    return {"succeeded": succeeded, "failed": failed}


def search(
    vec_type: str,
    query: str,
    mode: str = "hybrid",
    top_k: int = 10,
    filters: Optional[dict] = None,
    hybrid_weight: float = 0.7,
) -> List[dict]:
    """
    搜索向量库，返回原始结果列表。
    每条：{ data_id, text, score, metadata }
    """
    payload: Dict[str, Any] = {
        "type": vec_type,
        "query": query,
        "mode": mode,
        "top_k": top_k,
        "hybrid_weight": hybrid_weight,
    }
    if filters:
        payload["filters"] = filters

    resp = httpx.post(
        f"{settings.VECTOR_SERVICE_URL}/api/v1/search",
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def update(
    vec_type: str,
    data_id: str,
    text: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    payload: Dict[str, Any] = {"type": vec_type, "data_id": data_id}
    if text is not None:
        payload["text"] = text
    if metadata is not None:
        payload["metadata"] = metadata
    resp = httpx.put(
        f"{settings.VECTOR_SERVICE_URL}/api/v1/update",
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()


def delete(vec_type: str, data_id: str) -> None:
    resp = httpx.request(
        "DELETE",
        f"{settings.VECTOR_SERVICE_URL}/api/v1/item",
        json={"type": vec_type, "data_id": data_id},
        timeout=10,
    )
    resp.raise_for_status()
