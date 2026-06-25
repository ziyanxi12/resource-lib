"""
图片路由
POST /api/image/upload  接收图片文件 + 元数据，存文件并入库
"""

from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import image_service
from app.schemas.image import ImageUploadResponse

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
