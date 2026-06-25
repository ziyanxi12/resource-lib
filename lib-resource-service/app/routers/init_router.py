"""
初始化数据入库路由

POST /api/init          导入全部类型
POST /api/init/component  仅导入组件集
POST /api/init/icon       仅导入 SVG + 插画
POST /api/init/template   仅导入模版
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import init_service

router = APIRouter(prefix="/api/init", tags=["初始化入库"])


@router.post("")
def init_all(db: Session = Depends(get_db)):
    """
    一次性导入所有类型：组件集 / SVG / 插画 / 模版。
    各类型独立执行，单个类型失败不影响其他类型。
    """
    results = init_service.run_init_import(db)
    total_added   = sum(r.get("added",   0) for r in results.values())
    total_updated = sum(r.get("updated", 0) for r in results.values())
    return {
        "message": f"初始化完成：共新增 {total_added} 条，更新 {total_updated} 条",
        "detail":  results,
    }


@router.post("/component")
def init_component(db: Session = Depends(get_db)):
    """仅导入组件集（扫描 init/component/ 下所有子目录）"""
    result = init_service.import_components(db)
    return {"message": f"组件集导入完成：新增 {result['added']} 条，更新 {result['updated']} 条", **result}


@router.post("/icon")
def init_icon(db: Session = Depends(get_db)):
    """仅导入 SVG 和插画（读取 init/icon/svg.json 和 illustration.json）"""
    svg   = init_service.import_icons(db, "svg")
    illus = init_service.import_icons(db, "illustration")
    return {
        "message": f"图标导入完成：SVG 新增 {svg['added']} / 更新 {svg['updated']}，插画 新增 {illus['added']} / 更新 {illus['updated']}",
        "svg":          svg,
        "illustration": illus,
    }


@router.post("/template")
def init_template(db: Session = Depends(get_db)):
    """仅导入模版（读取 init/template/templates.json）"""
    result = init_service.import_templates(db)
    return {"message": f"模版导入完成：新增 {result['added']} 条，更新 {result['updated']} 条", **result}
