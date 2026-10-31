"""
资源导出路由
GET /api/export?format=json|csv|zip&type=&source_id=&group_id=&search=
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.enums import ResourceType
from app.services import export_service, operation_log_service
from app.services.operator import get_operator
from app.services.search_app_service import verify_app_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/export", tags=["资源导出"])


@router.get("")
def export_resources(
    request: Request,
    format: str = Query(..., description="导出格式: json | csv | zip"),
    type: Optional[str] = Query(None, description="资源类型名: icon/illus/image/file/person"),
    source_id: Optional[int] = Query(None, description="来源ID"),
    group_id: Optional[int] = Query(None, description="分组ID（递归含子孙）"),
    search: Optional[str] = Query(None, description="关键词"),
    db: Session = Depends(get_db),
):
    app_id = request.headers.get("octo-vs-token") or None
    if not verify_app_id(db, app_id):
        raise HTTPException(status_code=401, detail="无权限：app_id 缺失或无效")

    if format not in ("json", "csv", "zip"):
        raise HTTPException(status_code=400, detail="format 仅支持 json / csv / zip")

    resource_type_int = None
    if type:
        try:
            resource_type_int = int(ResourceType.from_name(type))
        except KeyError:
            raise HTTPException(status_code=400, detail=f"未知资源类型: {type}")

    resources, truncated = export_service.get_export_resources(
        db,
        resource_type=resource_type_int,
        source_id=source_id,
        search=search,
        group_id=group_id,
    )
    count = len(resources)

    # 在 session 关闭前预序列化为纯 dict + 收集文件路径
    items, file_entries, thumb_entries = export_service.serialize_resources(db, resources)

    account, name = get_operator(request)
    operation_log_service.create_log(
        db,
        source_id=source_id,
        resource_type=resource_type_int,
        operator=name,
        operator_account=account,
        action="export",
        target_type="resource",
        detail={
            "format": format,
            "type": type,
            "source_id": source_id,
            "group_id": group_id,
            "count": count,
            "truncated": truncated,
        },
    )

    headers = {
        "X-Export-Count": str(count),
        "X-Export-Truncated": "true" if truncated else "false",
    }

    if format == "json":
        filename = f"export_{type or 'all'}.json"
        return StreamingResponse(
            export_service.export_json_stream(items),
            media_type="application/json",
            headers={**headers, "Content-Disposition": f'attachment; filename="{filename}"'},
        )

    if format == "csv":
        filename = f"export_{type or 'all'}.csv"
        return StreamingResponse(
            export_service.export_csv_stream(items),
            media_type="text/csv; charset=utf-8",
            headers={**headers, "Content-Disposition": f'attachment; filename="{filename}"'},
        )

    filename = f"export_{type or 'all'}.zip"
    return StreamingResponse(
        export_service.export_zip_stream(items, file_entries, thumb_entries),
        media_type="application/zip",
        headers={**headers, "Content-Disposition": f'attachment; filename="{filename}"'},
    )
