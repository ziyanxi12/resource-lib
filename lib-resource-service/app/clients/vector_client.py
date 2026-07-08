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

_BATCH_SIZE = 200


def ingest(vec_type: str, items: List[dict]) -> dict:
    """
    批量写入向量库，自动分批（每批 _BATCH_SIZE 条）。
    items 每条：{ data_id, text, metadata }
    返回汇总后的 { succeeded: [...], failed: [...] }
    """
    if not items:
        return {"succeeded": [], "failed": []}

    total_batches = (len(items) + _BATCH_SIZE - 1) // _BATCH_SIZE
    logger.info("[ingest] 开始向量入库: type=%s  总计=%d条  共%d批", vec_type, len(items), total_batches)

    succeeded, failed = [], []
    for i in range(0, len(items), _BATCH_SIZE):
        batch     = items[i: i + _BATCH_SIZE]
        batch_num = i // _BATCH_SIZE + 1
        logger.info(
            "[ingest] 批次 %d/%d: type=%s  本批=%d条",
            batch_num, total_batches, vec_type, len(batch),
        )
        logger.debug(
            "[ingest] 批次 %d/%d payload: type=%s  items 前5条=%s",
            batch_num, total_batches, vec_type,
            [{"data_id": item["data_id"], "text": item.get("text", "")[:50]} for item in batch[:5]],
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
            logger.info(
                "[ingest] 批次 %d/%d 完成: 成功=%d  失败=%d  累计成功=%d",
                batch_num, total_batches, len(ok), len(fail), len(succeeded),
            )
        except Exception as e:
            logger.warning(
                "向量入库失败 (batch %d): %s, type=%s, 本批 data_id 前5条=%s",
                batch_num, type(e).__name__, vec_type,
                [item["data_id"] for item in batch[:5]],
            )
            logger.debug(
                "向量入库失败详情: type=%s  batch=%d  所有 data_id=%s  error=%s",
                vec_type, batch_num, [item["data_id"] for item in batch], str(e),
                exc_info=True,
            )
            failed.extend([{"data_id": it["data_id"], "error": str(e)} for it in batch])

    logger.info(
        "[ingest] 入库完成: type=%s  total=%d  succeeded=%d  failed=%d",
        vec_type, len(items), len(succeeded), len(failed),
    )
    return {"succeeded": succeeded, "failed": failed}


def search(
    vec_type: str,
    query: str,
    mode: Optional[str] = None,
    top_k: int = 10,
    filters: Optional[dict] = None,
    hybrid_weight: float = 0.7,
) -> List[dict]:
    """
    搜索向量库，返回原始结果列表。
    每条：{ data_id, text, score, metadata }
    """
    resolved_mode = mode or settings.VECTOR_SEARCH_MODE
    payload: Dict[str, Any] = {
        "type": vec_type,
        "query": query,
        "mode": resolved_mode,
        "top_k": top_k,
        "hybrid_weight": hybrid_weight,
    }
    if filters:
        payload["filters"] = filters

    logger.info(
        "[search] 发起搜索: type=%s  query='%s'  mode=%s  top_k=%d",
        vec_type, query, resolved_mode, top_k,
    )
    logger.debug("[search] 发起搜索详情: payload=%s", payload)

    try:
        resp = httpx.post(
            f"{settings.VECTOR_SERVICE_URL}/api/v1/search",
            json=payload,
            timeout=30,
            trust_env=False,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        
        # INFO：结果前3条摘要
        items = [
            {
                "data_id": item["data_id"],
                "score": round(item.get("score", 0), 4),
                "text": (item.get("text") or "")[:50],
            }
            for item in results[:3]
        ]
        logger.info("[search] 返回 %d 条结果，前3条: %s", len(results), items)
        
        # DEBUG：完整结果列表
        all_items = [
            {
                "data_id": item["data_id"],
                "score": round(item.get("score", 0), 4),
                "text": (item.get("text") or "")[:50],
            }
            for item in results
        ]
        logger.debug("[search] 返回完整结果: %s", all_items)
        
        return results
        
    except Exception as e:
        logger.warning(
            "[search] 搜索失败: %s, type=%s, query='%s'",
            type(e).__name__, vec_type, query,
        )
        logger.debug(
            "[search] 搜索失败详情: type=%s  query='%s'  payload=%s  error=%s",
            vec_type, query, payload, str(e),
            exc_info=True,
        )
        raise


def batch_search(
    vec_type: str,
    queries: List[str],
    mode: Optional[str] = None,
    top_k: int = 10,
    filters: Optional[dict] = None,
    hybrid_weight: float = 0.7,
) -> List[List[dict]]:
    """
    批量搜索，返回二维结果列表，顺序与 queries 一一对应。
    每条：{ data_id, text, score, metadata }
    """
    resolved_mode = mode or settings.VECTOR_SEARCH_MODE
    payload: Dict[str, Any] = {
        "type": vec_type,
        "queries": queries,
        "mode": resolved_mode,
        "top_k": top_k,
        "hybrid_weight": hybrid_weight,
    }
    if filters:
        payload["filters"] = filters

    logger.info(
        "[batch_search] 发起批量搜索: type=%s  queries=%s  mode=%s  top_k=%d",
        vec_type, queries, resolved_mode, top_k,
    )
    logger.debug("[batch_search] 发起批量搜索详情: payload=%s", payload)

    try:
        resp = httpx.post(
            f"{settings.VECTOR_SERVICE_URL}/api/v1/search/batch",
            json=payload,
            timeout=30,
            trust_env=False,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        
        # INFO：每组数量 + 第一组前3条
        if results:
            first_group = [
                {
                    "data_id": item["data_id"],
                    "score": round(item.get("score", 0), 4),
                    "text": (item.get("text") or "")[:50],
                }
                for item in results[0][:3]
            ]
            logger.info(
                "[batch_search] 返回 %d 组结果: 第1组(%d条)前3条=%s",
                len(results), len(results[0]), first_group,
            )
        else:
            logger.info("[batch_search] 返回 0 组结果")
        
        # DEBUG：完整结果（每组全部）
        result_detail = []
        for i, group in enumerate(results):
            items = [
                {
                    "data_id": item["data_id"],
                    "score": round(item.get("score", 0), 4),
                    "text": (item.get("text") or "")[:50],
                }
                for item in group
            ]
            result_detail.append(f"第{i+1}组({len(group)}条): {items}")
        logger.debug("[batch_search] 返回完整结果:\n%s", "\n".join(result_detail))
        
        return results
        
    except Exception as e:
        logger.warning(
            "[batch_search] 批量搜索失败: %s, type=%s, queries前3条=%s",
            type(e).__name__, vec_type, queries[:3],
        )
        logger.debug(
            "[batch_search] 批量搜索失败详情: type=%s  queries=%s  payload=%s  error=%s",
            vec_type, queries, payload, str(e),
            exc_info=True,
        )
        raise


def update(
    vec_type: str,
    data_id: str,
    text: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    logger.info("[update] 更新向量: type=%s  data_id=%s", vec_type, data_id)
    payload: Dict[str, Any] = {"type": vec_type, "data_id": data_id}
    if text is not None:
        payload["text"] = text
    if metadata is not None:
        payload["metadata"] = metadata
    
    logger.debug("[update] 更新详情: payload=%s", payload)
    
    try:
        resp = httpx.put(
            f"{settings.VECTOR_SERVICE_URL}/api/v1/update",
            json=payload,
            timeout=30,
            trust_env=False,
        )
        resp.raise_for_status()
    except Exception as e:
        logger.warning(
            "[update] 更新失败: %s, type=%s, data_id=%s",
            type(e).__name__, vec_type, data_id,
        )
        logger.debug(
            "[update] 更新失败详情: type=%s  data_id=%s  payload=%s  error=%s",
            vec_type, data_id, payload, str(e),
            exc_info=True,
        )
        raise


def delete(vec_type: str, data_id: str) -> None:
    logger.info("[delete] 删除向量: type=%s  data_id=%s", vec_type, data_id)
    logger.debug("[delete] 删除详情: type=%s  data_id=%s", vec_type, data_id)
    
    try:
        resp = httpx.request(
            "DELETE",
            f"{settings.VECTOR_SERVICE_URL}/api/v1/item",
            json={"type": vec_type, "data_id": data_id},
            timeout=10,
            trust_env=False,
        )
        resp.raise_for_status()
    except Exception as e:
        logger.warning(
            "[delete] 删除失败: %s, type=%s, data_id=%s",
            type(e).__name__, vec_type, data_id,
        )
        logger.debug(
            "[delete] 删除失败详情: type=%s  data_id=%s  error=%s",
            vec_type, data_id, str(e),
            exc_info=True,
        )
        raise


# ──────────────────────────────────────────────────────────────────
# 向量库 ID 查询（精准补录用）
# ──────────────────────────────────────────────────────────────────

def get_ids(vec_type: str, limit: int = 1000, offset: int = 0) -> dict:
    """
    获取向量库所有 data_id（分页）
    
    返回：{"total": 4523, "ids": [...], "has_more": true}
    """
    logger.info("[get_ids] 查询向量库 ID: type=%s limit=%d offset=%d", vec_type, limit, offset)
    logger.debug("[get_ids] 查询详情: type=%s  limit=%d  offset=%d", vec_type, limit, offset)
    
    try:
        resp = httpx.get(
            f"{settings.VECTOR_SERVICE_URL}/api/v1/ids",
            params={"type": vec_type, "limit": limit, "offset": offset},
            timeout=10,
            trust_env=False,
        )
        resp.raise_for_status()
        data = resp.json()
        
        # INFO：返回数量
        logger.info("[get_ids] 返回 %d 条 ID", len(data.get("ids", [])))
        
        # DEBUG：完整 IDs
        logger.debug("[get_ids] 返回完整IDs: %s", data.get("ids", []))
        
        return data
        
    except Exception as e:
        logger.warning(
            "[get_ids] 查询失败: %s, type=%s, limit=%d, offset=%d",
            type(e).__name__, vec_type, limit, offset,
        )
        logger.debug(
            "[get_ids] 查询失败详情: type=%s  limit=%d  offset=%d  error=%s",
            vec_type, limit, offset, str(e),
            exc_info=True,
        )
        raise


def get_all_ids(vec_type: str, batch_size: int = 1000) -> List[str]:
    """
    自动分页获取向量库所有 data_id
    
    适用场景：向量库有 4000+ 条数据，自动分批获取
    """
    logger.info("[get_all_ids] 开始获取全部 ID: type=%s", vec_type)
    all_ids = []
    offset = 0
    
    try:
        while True:
            result = get_ids(vec_type, limit=batch_size, offset=offset)
            ids = result.get("ids", [])
            all_ids.extend(ids)
            
            # DEBUG：每批详细内容
            logger.debug(
                "[get_all_ids] 第%d批: 获取%d条 IDs前10=%s",
                offset // batch_size + 1, len(ids), ids[:10],
            )
            
            if not result.get("has_more", False):
                break
            
            offset += batch_size
        
        logger.info("[get_all_ids] 获取完成: type=%s total=%d", vec_type, len(all_ids))
        return all_ids
        
    except Exception as e:
        logger.warning(
            "[get_all_ids] 获取失败: %s, type=%s",
            type(e).__name__, vec_type,
        )
        logger.debug(
            "[get_all_ids] 获取失败详情: type=%s  error=%s",
            vec_type, str(e),
            exc_info=True,
        )
        raise


def check_ids_missing(vec_type: str, ids: List[str]) -> List[str]:
    """
    批量检查缺失的 data_id
    
    返回：缺失的 ID 列表
    """
    if not ids:
        return []
    
    logger.info("[check_ids_missing] 批量检查: type=%s count=%d", vec_type, len(ids))
    
    try:
        resp = httpx.post(
            f"{settings.VECTOR_SERVICE_URL}/api/v1/ids/check",
            json={"type": vec_type, "ids": ids},
            timeout=30,
            trust_env=False,
        )
        resp.raise_for_status()
        data = resp.json()
        missing = data.get("missing", [])
        
        # INFO：缺失数量
        logger.info("[check_ids_missing] 缺失 %d 条", len(missing))
        
        # DEBUG：完整缺失 IDs
        logger.debug("[check_ids_missing] 缺失IDs详情: %s", missing)
        
        return missing
        
    except Exception as e:
        logger.warning(
            "[check_ids_missing] 检查失败: %s, type=%s, count=%d",
            type(e).__name__, vec_type, len(ids),
        )
        logger.debug(
            "[check_ids_missing] 检查失败详情: type=%s  ids=%s  error=%s",
            vec_type, ids, str(e),
            exc_info=True,
        )
        raise
