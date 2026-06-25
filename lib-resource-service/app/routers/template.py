"""
模版路由
POST /api/template/upload  接收名称、描述、hex 文本，写文件并入库
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import template_service
from app.schemas.template import TemplateUploadRequest, TemplateUploadResponse

router = APIRouter(prefix="/api/template", tags=["模版"])


@router.post("/upload", response_model=TemplateUploadResponse)
def upload_template(body: TemplateUploadRequest, db: Session = Depends(get_db)):
    """上传模版 hex 数据，写入文件系统并记录到数据库"""
    result = template_service.upload_template(
        db=db,
        name=body.name,
        description=body.description,
        hex_data=body.hex_data,
    )
    return TemplateUploadResponse(**result)
