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
        logger.debug(
            "[ingest] 发起入库: type=%s  batch=%d  items=%d条",
            vec_type, i // _BATCH_SIZE, len(batch),
        )
        try:
            resp = httpx.post(
                f"{settings.VECTOR_SERVICE_URL}/api/v1/ingest",
                json={"type": vec_type, "items": batch},
                timeout=60,
                trust_env=False,
            )
            resp.raise_for_status()
            data = resp.json()
            ok   = data.get("succeeded", [])
            fail = data.get("failed", [])
            succeeded.extend(ok)
            failed.extend(fail)
            logger.debug(
                "[ingest] 批次结果: succeeded=%d  failed=%d",
                len(ok), len(fail),
            )
        except Exception as e:
            logger.warning("向量入库失败 (batch %d): %s", i // _BATCH_SIZE, e)
            failed.extend([{"data_id": it["data_id"], "error": str(e)} for it in batch])

    logger.info(
        "[ingest] 入库完成: type=%s  total=%d  succeeded=%d  failed=%d",
        vec_type, len(items), len(succeeded), len(failed),
    )
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

    logger.debug(
        "[search] 发起搜索: type=%s  query=%r  mode=%s  top_k=%d",
        vec_type, query, mode, top_k,
    )

    resp = httpx.post(
        f"{settings.VECTOR_SERVICE_URL}/api/v1/search",
        json=payload,
        timeout=30,
        trust_env=False,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    logger.debug("[search] 返回 %d 条结果", len(results))
    return results


def update(
    vec_type: str,
    data_id: str,
    text: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    logger.debug("[update] 更新向量: type=%s  data_id=%s", vec_type, data_id)
    payload: Dict[str, Any] = {"type": vec_type, "data_id": data_id}
    if text is not None:
        payload["text"] = text
    if metadata is not None:
        payload["metadata"] = metadata
    resp = httpx.put(
        f"{settings.VECTOR_SERVICE_URL}/api/v1/update",
        json=payload,
        timeout=30,
        trust_env=False,
    )
    resp.raise_for_status()


def delete(vec_type: str, data_id: str) -> None:
    logger.debug("[delete] 删除向量: type=%s  data_id=%s", vec_type, data_id)
    resp = httpx.request(
        "DELETE",
        f"{settings.VECTOR_SERVICE_URL}/api/v1/item",
        json={"type": vec_type, "data_id": data_id},
        timeout=10,
        trust_env=False,
    )
    resp.raise_for_status()
