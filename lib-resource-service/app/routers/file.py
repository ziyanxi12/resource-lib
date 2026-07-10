"""
文件路由
POST /api/file/upload  接收文件 + PNG 缩略图 + 元数据，存文件并入库
"""

import json
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import file_service
from app.schemas.file import FileUploadResponse, BatchUploadResponse

router = APIRouter(prefix="/api/file", tags=["文件"])


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file:        UploadFile     = File(...,  description="文件（任意类型）"),
    thumbnail:   UploadFile     = File(...,  description="缩略图（PNG 格式，必填）"),
    name:        str            = Form(...,  description="文件名称"),
    description: Optional[str]  = Form(None, description="文件描述"),
    tags:        Optional[str]  = Form(None, description="标签（JSON 数组字符串）"),
    created_by:  Optional[str]  = Form(None, description="上传人"),
    db: Session = Depends(get_db),
):
    """
    上传文件，保存到文件系统，记录到数据库
    - file: 任意类型文件
    - thumbnail: PNG 缩略图（必填，强制校验 mime_type）
    - tags: JSON 数组字符串，如 ["文档", "产品"]
    """
    if thumbnail.content_type != "image/png":
        raise HTTPException(status_code=400, detail="缩略图必须为 PNG 格式")

    tags_list = []
    if tags:
        try:
            tags_list = json.loads(tags)
            if not isinstance(tags_list, list):
                raise HTTPException(status_code=400, detail="tags 必须为 JSON 数组")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="tags 参数必须是有效的 JSON 数组")

    result = await file_service.upload_file(
        db=db,
        file=file,
        thumbnail=thumbnail,
        name=name,
        description=description,
        tags=tags_list,
        created_by=created_by,
    )
    return FileUploadResponse(**result)


@router.post("/batch-upload", response_model=BatchUploadResponse)
async def batch_upload_files(
    files:       List[UploadFile] = File(...,  description="文件列表（任意类型）"),
    thumbnails:  List[UploadFile] = File(...,  description="缩略图列表（PNG，按索引一一对应）"),
    items:       str              = Form(...,  description="元数据 JSON 数组：[{name, description?, tags?}]"),
    created_by:  Optional[str]    = Form(None, description="上传人"),
    db: Session = Depends(get_db),
):
    """
    批量上传文件
    - files 和 thumbnails 按索引一一对应
    - items 格式：[{"name":"文档1","description":"描述","tags":["标签1"]}, ...]
    - 缩略图强制 PNG 格式
    """
    if len(files) != len(thumbnails):
        raise HTTPException(
            status_code=400,
            detail=f"文件数量({len(files)})与缩略图数量({len(thumbnails)})不一致"
        )

    try:
        items_list = json.loads(items)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="items 参数必须是有效的 JSON 数组")

    if not isinstance(items_list, list):
        raise HTTPException(status_code=400, detail="items 必须为 JSON 数组")

    if len(items_list) != len(files):
        raise HTTPException(
            status_code=400,
            detail=f"文件数量({len(files)})与元数据数量({len(items_list)})不一致"
        )

    for i, thumb in enumerate(thumbnails):
        if thumb.content_type != "image/png":
            raise HTTPException(
                status_code=400,
                detail=f"第 {i + 1} 个缩略图必须为 PNG 格式"
            )

    for i, item in enumerate(items_list):
        if not item.get("name", "").strip():
            raise HTTPException(
                status_code=400,
                detail=f"第 {i + 1} 个文件名称不能为空"
            )

    result = await file_service.batch_upload_files(
        db=db,
        files=files,
        thumbnails=thumbnails,
        items=items_list,
        created_by=created_by,
    )
    return BatchUploadResponse(**result)