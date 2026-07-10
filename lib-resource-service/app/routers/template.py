"""
模版路由
POST /api/template/upload        接收名称、描述、hex 文本，写文件并入库（单次上传）
POST /api/template/batch-upload  批量上传模版（预览图 + hex 数据 + 元数据）
"""

import json
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import template_service
from app.schemas.template import TemplateUploadRequest, TemplateUploadResponse, BatchUploadTemplateResponse

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


@router.post("/batch-upload", response_model=BatchUploadTemplateResponse)
async def batch_upload_templates(
    preview_files: List[UploadFile] = File(..., description="预览图列表（仅 png）"),
    hex_datas: str = Form(..., description="JSON数组：['hex文本1', 'hex文本2']"),
    items: str = Form(..., description="JSON数组：[{name, description?, tags?}]"),
    created_by: Optional[str] = Form(None, description="上传人"),
    db: Session = Depends(get_db),
):
    """
    批量上传模版
    - preview_files、hex_datas、items 按索引一一对应
    - 预览图仅允许 png 格式
    """
    try:
        hex_datas_list = json.loads(hex_datas)
        items_list = json.loads(items)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 解析失败: {str(e)}")
    
    result = await template_service.batch_upload_templates(
        db=db,
        preview_files=preview_files,
        hex_datas=hex_datas_list,
        items=items_list,
        created_by=created_by,
    )
    return BatchUploadTemplateResponse(**result)
