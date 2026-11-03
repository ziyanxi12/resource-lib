#!/usr/bin/env python3
"""设计系统种子导入：把 design-system-demo 的 3 个 design-system.json + 4 张内置封面
拷入 FILE_ROOT_DIR/design-systems/，并写入 design_systems 表（幂等，--force 覆盖）。

用法（在 lib-resource-service 目录下）：
    .venv/bin/python scripts/seed_design_systems.py            # 已存在的 slug 跳过
    .venv/bin/python scripts/seed_design_systems.py --force    # 覆盖 meta 与文件
"""

import argparse
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base  # noqa: E402
from app.models.design_system import DesignSystem  # noqa: E402
from app.models.ds_whitelist import DsWhitelistAccount  # noqa: E402
from app.services import design_system_service as svc  # noqa: E402
from app.services import ds_whitelist_service  # noqa: E402
from app.config import settings  # noqa: E402

DEFAULT_DEMO_DIR = "/Users/h30072573/Downloads/design-system-demo"

SEEDS = [
    {
        "slug": "h-design",
        "name": "H Design 官网设计规范",
        "desc": "H Design 官网设计规范，转换自 H Design 规范 Skill。",
        "author": "罗唯",
        "usage": 143,
        "cover": "cover-blue.jpg",
        "default": True,
    },
    {
        "slug": "ict-pc",
        "name": "ICT领域PC端设计规范",
        "desc": "ICT领域PC端设计规范，转换自 ICT PC 规范 Skill。",
        "author": "黄舒凡",
        "usage": 158,
        "cover": "cover-blue.jpg",
        "default": False,
    },
    {
        "slug": "text-to-ui",
        "name": "HarmonyOS PC 客户端规范（text-to-ui-html）",
        "desc": "用于生成和修改 HarmonyOS PC 动态 HTML 页面，或把已确认的交互 Demo 规范化为标准组件、Pattern 和 Token 的实现。",
        "author": "ahai66666",
        "usage": 0,
        "cover": "cover-cyan.jpg",
        "default": False,
    },
]

# 设计系统管理台专属白名单（与原 whitelist_accounts 隔离；白名单外账号无法进入管理台）
DS_WHITELIST_SEEDS = [
    {"account": "admin", "nick_name": "管理员", "role": "super", "remark": "种子账号"},
    {"account": "zhangsan", "nick_name": "张三", "role": "super", "remark": "种子账号"},
    {"account": "lisi", "nick_name": "李四", "role": "admin", "remark": "种子账号"},
    {"account": "guest", "nick_name": "访客", "role": "admin", "remark": "种子账号"},
    {"account": "wangwu", "nick_name": "王五", "role": "admin", "remark": "种子账号"},
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo-dir", default=DEFAULT_DEMO_DIR, help="design-system-demo 目录")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的记录与文件")
    args = parser.parse_args()

    systems_dir = os.path.join(args.demo_dir, "design-system-app", "public", "design-systems", "detail", "systems")
    covers_dir = os.path.join(args.demo_dir, "design-system-admin", "public", "covers")

    # 1. 内置封面 → FILE_ROOT_DIR/design-systems/covers/
    cover_dest = os.path.join(settings.FILE_ROOT_DIR, "design-systems", "covers")
    os.makedirs(cover_dest, exist_ok=True)
    for f in svc.BUILTIN_COVERS:
        src = os.path.join(covers_dir, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(cover_dest, f))
            print("封面: %s" % f)
        else:
            print("警告: 封面缺失 %s" % src)

    # 2. 种子系统（脚本独立运行时自建缺失表，与服务端 create_all 等价）
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for seed in SEEDS:
            slug = seed["slug"]
            src_json = os.path.join(systems_dir, slug, "design-system.json")
            if not os.path.exists(src_json):
                print("警告: JSON 缺失 %s" % src_json)
                continue

            with open(src_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            errors = svc.validate_design_system_json(data)
            if errors:
                print("跳过 %s: 校验失败 %s" % (slug, errors))
                continue

            row = db.query(DesignSystem).filter(
                DesignSystem.slug == slug, DesignSystem.is_deleted == 0
            ).first()
            if row and not args.force:
                print("跳过 %s: 已存在（--force 覆盖）" % slug)
                continue

            size = os.path.getsize(src_json)
            svc.save_json_file(slug, data, size)

            if row:
                row.name = seed["name"]
                row.desc = seed["desc"]
                row.author = seed["author"]
                row.usage = seed["usage"]
                row.cover = seed["cover"]
                row.is_default = seed["default"]
                row.file_size = size
                row.updated_by = "seed"
            else:
                db.add(DesignSystem(
                    slug=slug,
                    name=seed["name"],
                    desc=seed["desc"],
                    author=seed["author"],
                    usage=seed["usage"],
                    cover=seed["cover"],
                    is_default=seed["default"],
                    file_path=svc.rel_path(slug),
                    file_size=size,
                    created_by="seed",
                    updated_by="seed",
                ))
            db.commit()
            print("导入: %s（%s bytes）" % (slug, size))

        # 3. 设计系统白名单种子（幂等，与原 whitelist_accounts 隔离）
        for seed in DS_WHITELIST_SEEDS:
            existing = ds_whitelist_service.get_account(db, seed["account"])
            if existing and not args.force:
                continue
            if existing:
                ds_whitelist_service.update_account(
                    db, existing, nick_name=seed["nick_name"], role=seed["role"]
                )
            else:
                ds_whitelist_service.create_account(
                    db, account=seed["account"], nick_name=seed["nick_name"],
                    remark=seed["remark"], role=seed["role"],
                )
            print("白名单: %s（%s）" % (seed["account"], seed["role"]))
    finally:
        db.close()

    print("完成。存储目录: %s/design-systems" % settings.FILE_ROOT_DIR)


if __name__ == "__main__":
    main()
