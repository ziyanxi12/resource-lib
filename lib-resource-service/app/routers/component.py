"""
组件集路由
GET  /api/component/list   读取 component_map.json，返回可选组件库列表
POST /api/component/sync   触发完整同步流程
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import component_service
from app.schemas.component import ComponentSyncRequest, ComponentSyncResponse

router = APIRouter(prefix="/api/component", tags=["组件集"])


@router.get("/list")
def list_component_map():
    """返回 component_map.json 中配置的所有组件库"""
    return {"items": component_service.get_component_map()}


@router.post("/sync", response_model=ComponentSyncResponse)
async def sync_component(body: ComponentSyncRequest, db: Session = Depends(get_db)):
    """
    完整同步流程：获取版本 → 下载 pix → 拆解 → 读 component_index.json → 写 DB → 向量化
    Mock 模式下外部 API 返回模拟数据，拆解后生成占位 component_index.json，其余流程相同。
    """
    component_map = component_service.get_component_map()
    valid_keys    = {item["fileKey"] for item in component_map}
    if body.file_key not in valid_keys:
        raise HTTPException(status_code=400, detail=f"未知 fileKey: {body.file_key}")

    result = await component_service.sync_component(db, body.file_key)

    return ComponentSyncResponse(
        file_key=body.file_key,
        added=result["added"],
        updated=result["updated"],
        message=f"同步完成：新增 {result['added']} 个，更新 {result['updated']} 个",
    )
