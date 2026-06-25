"""
SVG / 插画路由
POST /api/icon/sync  拉取图标数据，写 JSON 文件、入库、向量化
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import icon_service
from app.schemas.icon import IconSyncRequest, IconSyncResponse

router = APIRouter(prefix="/api/icon", tags=["SVG/插画"])


@router.post("/sync", response_model=IconSyncResponse)
async def sync_icons(body: IconSyncRequest, db: Session = Depends(get_db)):
    """同步 SVG 或插画数据：拉取 → 保存 JSON → 入库 → 向量化"""
    result = await icon_service.sync_icons(db, body.type)

    return IconSyncResponse(
        type=body.type,
        added=result["added"],
        updated=result["updated"],
        message=f"同步完成：新增 {result['added']} 条，更新 {result['updated']} 条",
    )
