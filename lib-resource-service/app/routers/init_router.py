"""
初始化数据入库路由

POST /api/init            导入全部类型
POST /api/init/component  仅导入组件集
POST /api/init/icon       仅导入 SVG 图标
POST /api/init/illus      仅导入插画
POST /api/init/template   仅导入模版
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import init_service

router = APIRouter(prefix="/api/init", tags=["初始化入库"])


@router.post("")
def init_all(db: Session = Depends(get_db), skip_vector: bool = Query(False)):
    """
    一次性导入所有类型：组件集 / SVG / 插画 / 模版。
    skip_vector=true 时只刷 DB，不更新向量库。
    """
    results = init_service.run_init_import(db, skip_vector=skip_vector)
    total_added   = sum(r.get("added",   0) for r in results.values())
    total_updated = sum(r.get("updated", 0) for r in results.values())
    return {
        "message": f"初始化完成：共新增 {total_added} 条，更新 {total_updated} 条",
        "detail":  results,
    }


@router.post("/component")
def init_component(db: Session = Depends(get_db), skip_vector: bool = Query(False)):
    """仅导入组件集。"""
    result = init_service.import_components(db, skip_vector=skip_vector)
    return {"message": f"组件集导入完成：新增 {result['added']} 条，更新 {result['updated']} 条", **result}


@router.post("/icon")
def init_icon(db: Session = Depends(get_db), skip_vector: bool = Query(False)):
    """仅导入 SVG 图标。"""
    result = init_service.import_icons(db, skip_vector=skip_vector)
    return {"message": f"SVG 导入完成：新增 {result['added']} 条，更新 {result['updated']} 条", **result}


@router.post("/illus")
def init_illus(db: Session = Depends(get_db), skip_vector: bool = Query(False)):
    """仅导入插画。"""
    result = init_service.import_illus(db, skip_vector=skip_vector)
    return {"message": f"插画导入完成：新增 {result['added']} 条，更新 {result['updated']} 条", **result}


@router.post("/template")
def init_template(db: Session = Depends(get_db), skip_vector: bool = Query(False)):
    """仅导入模版。"""
    result = init_service.import_templates(db, skip_vector=skip_vector)
    return {"message": f"模版导入完成：新增 {result['added']} 条，更新 {result['updated']} 条", **result}


@router.post("/image")
def init_image(db: Session = Depends(get_db), skip_vector: bool = Query(False)):
    """扫描 storage/image/ 目录，批量入库图片。"""
    result = init_service.import_images(db, skip_vector=skip_vector)
    return {"message": f"图片导入完成：新增 {result['added']} 条，更新 {result['updated']} 条", **result}
