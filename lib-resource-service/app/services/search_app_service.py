import json
import logging
import os
import secrets
from datetime import datetime
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.search_app import SearchApp

logger = logging.getLogger(__name__)

APP_ID_PREFIX = "octo_vs_"


def _generate_app_id() -> str:
    return APP_ID_PREFIX + secrets.token_hex(16)


def get_apps(db: Session, is_active: Optional[int] = None) -> List[SearchApp]:
    query = db.query(SearchApp)
    if is_active is not None:
        query = query.filter(SearchApp.is_active == is_active)
    return query.order_by(SearchApp.created_at.desc()).all()


def get_app_by_id(db: Session, app_id_pk: int) -> Optional[SearchApp]:
    return db.query(SearchApp).filter(SearchApp.id == app_id_pk).first()


def create_app(db: Session, name: str, remark: Optional[str] = None) -> SearchApp:
    if not name or not name.strip():
        raise ValueError("name is required")

    for _ in range(5):
        app = SearchApp(
            app_id=_generate_app_id(),
            name=name.strip(),
            remark=remark,
            is_active=1,
        )
        db.add(app)
        try:
            db.commit()
            db.refresh(app)
            return app
        except IntegrityError:
            db.rollback()
            continue
    raise RuntimeError("生成 app_id 失败（重试 5 次仍冲突）")


def import_app(
    db: Session,
    app_id: str,
    name: str,
    remark: Optional[str] = None,
    is_active: int = 1,
    created_at: Optional[str] = None,
    updated_at: Optional[str] = None,
) -> dict:
    """指定 app_id 导入，已存在则跳过（幂等）。返回 {action: created/skipped, app}"""
    existing = db.query(SearchApp).filter(SearchApp.app_id == app_id).first()
    if existing:
        return {"action": "skipped", "app": existing}

    parsed_created = _parse_dt(created_at) or datetime.now()
    parsed_updated = _parse_dt(updated_at) or parsed_created

    app = SearchApp(
        app_id=app_id,
        name=name,
        remark=remark,
        is_active=is_active,
        created_at=parsed_created,
        updated_at=parsed_updated,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return {"action": "created", "app": app}


def update_app(db: Session, app_id_pk: int, data: dict) -> Optional[SearchApp]:
    app = get_app_by_id(db, app_id_pk)
    if not app:
        return None

    for key, value in data.items():
        if key in ("name", "remark"):
            setattr(app, key, value)

    db.commit()
    db.refresh(app)
    return app


def delete_app(db: Session, app_id_pk: int) -> bool:
    app = get_app_by_id(db, app_id_pk)
    if not app:
        return False
    app.is_active = 0
    db.commit()
    return True


def export_apps(db: Session) -> List[dict]:
    apps = db.query(SearchApp).order_by(SearchApp.id.asc()).all()
    return [
        {
            "app_id": app.app_id,
            "name": app.name,
            "remark": app.remark,
            "is_active": app.is_active,
            "created_at": app.created_at.isoformat() if app.created_at else None,
            "updated_at": app.updated_at.isoformat() if app.updated_at else None,
        }
        for app in apps
    ]


def import_apps_from_file(db: Session) -> dict:
    """读取 SEARCH_APPS_IMPORT_FILE 指定的 JSON 文件，逐条导入（幂等）。文件不存在则跳过。"""
    from app.config import settings

    file_path = settings.SEARCH_APPS_IMPORT_FILE
    if not os.path.exists(file_path):
        return {"imported": 0, "skipped": 0, "message": "文件不存在，跳过"}

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        return {"imported": 0, "skipped": 0, "message": "JSON 格式错误，期望数组"}

    imported = 0
    skipped = 0
    for item in data:
        app_id = item.get("app_id")
        name = item.get("name")
        if not app_id or not name:
            continue
        result = import_app(
            db,
            app_id=app_id,
            name=name,
            remark=item.get("remark"),
            is_active=item.get("is_active", 1),
            created_at=item.get("created_at"),
            updated_at=item.get("updated_at"),
        )
        if result["action"] == "created":
            imported += 1
        else:
            skipped += 1

    return {"imported": imported, "skipped": skipped, "total": len(data)}


def _parse_dt(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return None
