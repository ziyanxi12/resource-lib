"""
统一批量上传路由
POST /api/upload?type=component|icon|illus|template|image|file
"""

import json
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.enums import ResourceType
from app.services import upload_service
from app.schemas.upload import BatchUploadResponse
from app.config import settings

router = APIRouter(prefix="/api/upload", tags=["批量上传"])


@router.post("", response_model=BatchUploadResponse)
async def batch_upload(
    type: str = Query(..., description="资源类型：icon/illus/template/image/file"),
    files: List[UploadFile] = File(..., description="资源文件列表"),
    thumbnails: List[UploadFile] = File(..., description="缩略图列表（PNG）"),
    items: str = Form(..., description="JSON数组：[{name, group_id, width, height, ...}]"),
    source_id: int = Form(..., description="来源ID"),
    created_by: Optional[str] = Form(None, description="创建者"),
    db: Session = Depends(get_db),
):
    """
    统一批量上传接口
    
    - files、thumbnails、items 按索引一一对应
    - 缩略图仅允许 PNG 格式
    - items 格式：[{"name":"资源名","group_id":1,"width":24,"height":24,...}, ...]
    """
    # 校验类型
    try:
        resource_type = ResourceType.from_name(type)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"未知资源类型: {type}")

    # 解析 items
    try:
        items_list = json.loads(items)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON 解析失败: {str(e)}")

    if not isinstance(items_list, list):
        raise HTTPException(status_code=400, detail="items 必须为 JSON 数组")

    # 获取生效的上传限制
    max_count, max_zip_mb, max_file_mb = settings.get_effective_upload_limit()

    # 校验条目数量
    if len(items_list) > max_count:
        raise HTTPException(
            status_code=400,
            detail=f"单次上传最多 {max_count} 条，当前 {len(items_list)} 条"
        )

    # 校验数量一致性
    if len(files) != len(thumbnails):
        raise HTTPException(
            status_code=400,
            detail=f"文件数量({len(files)})与缩略图数量({len(thumbnails)})不一致"
        )

    if len(items_list) != len(files):
        raise HTTPException(
            status_code=400,
            detail=f"元数据数量({len(items_list)})与文件数量({len(files)})不一致"
        )

    # 校验缩略图格式
    for i, thumb in enumerate(thumbnails):
        if thumb.filename and thumb.content_type != "image/png":
            raise HTTPException(
                status_code=400,
                detail=f"第 {i + 1} 个缩略图必须为 PNG 格式"
            )

    # 校验单文件大小
    for i, file in enumerate(files):
        if file.filename and file.size is not None:
            max_file_bytes = max_file_mb * 1024 * 1024
            if file.size > max_file_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"第 {i + 1} 个文件大小超过限制 ({max_file_mb}MB)"
                )

    # 校验必填字段
    for i, item in enumerate(items_list):
        if not item.get("name", "").strip():
            raise HTTPException(status_code=400, detail=f"第 {i + 1} 条名称不能为空")
        if item.get("group_id") is None:
            raise HTTPException(status_code=400, detail=f"第 {i + 1} 条分组ID不能为空")
        if item.get("width") is None:
            raise HTTPException(status_code=400, detail=f"第 {i + 1} 条宽度不能为空")
        if item.get("height") is None:
            raise HTTPException(status_code=400, detail=f"第 {i + 1} 条高度不能为空")
        
        # 校验宽高为正数
        try:
            w = float(item.get("width", 0))
            h = float(item.get("height", 0))
            if w <= 0 or h <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail=f"第 {i + 1} 条宽高必须为正数")

        # 校验文件路径或链接至少有一个
        if not item.get("file_path") and not item.get("file_url"):
            raise HTTPException(status_code=400, detail=f"第 {i + 1} 条文件路径或链接至少填一个")

    # 调用统一上传服务
    result = await upload_service.batch_upload(
        db=db,
        resource_type=resource_type,
        files=files,
        thumbnails=thumbnails,
        items=items_list,
        source_id=source_id,
        created_by=created_by,
    )

    return BatchUploadResponse(**result)