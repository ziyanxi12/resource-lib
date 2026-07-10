"""
图片路由
POST /api/image/upload      接收图片文件 + 元数据，存文件并入库
POST /api/image/batch-upload 批量上传图片
"""

import json
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import image_service
from app.schemas.image import ImageUploadResponse, BatchUploadResponse

router = APIRouter(prefix="/api/image", tags=["图片"])


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    file:        UploadFile      = File(...,  description="图片文件"),
    name:        str             = Form(...,  description="图片名称"),
    description: Optional[str]  = Form(None, description="图片描述"),
    created_by:  Optional[str]  = Form(None, description="上传人"),
    db: Session = Depends(get_db),
):
    """上传图片，保存到文件系统，提取尺寸，记录到数据库"""
    result = await image_service.upload_image(
        db=db,
        file=file,
        name=name,
        description=description,
        created_by=created_by,
    )
    return ImageUploadResponse(**result)


@router.post("/batch-upload", response_model=BatchUploadResponse)
async def batch_upload_images(
    files:       List[UploadFile] = File(...,  description="图片文件列表"),
    items:       str              = Form(...,  description="JSON数组：[{name, description?, tags?}]"),
    created_by:  Optional[str]    = Form(None, description="上传人"),
    db: Session = Depends(get_db),
):
    """
    批量上传图片
    - files 和 items 按索引一一对应
    - items 格式：[{"name":"图片1","description":"描述","tags":["标签1"]}, ...]
    - tags 支持新建，数组格式
    """
    try:
        items_list = json.loads(items)
    except json.JSONDecodeError:
        raise ValueError("items 参数必须是有效的 JSON 数组")
    
    result = await image_service.batch_upload_images(
        db=db,
        files=files,
        items=items_list,
        created_by=created_by,
    )
    return BatchUploadResponse(**result)
