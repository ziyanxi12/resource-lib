import logging
from typing import TYPE_CHECKING, Dict, List, Tuple

from app.config import settings

if TYPE_CHECKING:
    from app.enums import ResourceType
    from app.models.resource import Resource

logger = logging.getLogger(__name__)


def ingest_vectors(
    resource_type: "ResourceType",
    pairs: List[Tuple["Resource", dict]],
    *,
    skip_vector: bool = False,
) -> None:
    """
    批量向量入库，所有类型统一入口。
    pairs: [(Resource ORM 对象, 原始 raw dict), ...]
    raw 在 init 场景携带 JSON 原始字段；PUT 更新场景传 {} 即可。
    异常只 warning，不影响主流程。
    """
    if skip_vector or not settings.VECTOR_SERVICE_ENABLED:
        return
    
    if not pairs:
        return
    
    from app.enums import ResourceType
    from app.services.resource_service import build_vector_text
    
    vec_type_map = {
        ResourceType.component: "component",
        ResourceType.template: "template",
        ResourceType.icon: "icon",
        ResourceType.illus: "illustration",
        ResourceType.image: "image",
        ResourceType.file: "file",
    }
    
    vec_type = vec_type_map.get(resource_type)
    if vec_type is None:
        return
    
    items = [
        {
            "data_id":  str(res.id),
            "text":     res.vector_text or build_vector_text(res),
            "metadata": {
                "source_id": res.source_id,
                "group_id":  res.group_id,
                "tags":      [t.tag for t in res.tags],
            },
        }
        for res, raw in pairs
    ]
    
    try:
        from app.clients import vector_client
        result = vector_client.ingest(vec_type, items)
        logger.info(
            "向量入库完成 type=%s: 成功 %d 条，失败 %d 条",
            vec_type, len(result["succeeded"]), len(result["failed"]),
        )
    except Exception as e:
        logger.warning("向量入库异常（不影响 DB）type=%s: %s", vec_type, e)