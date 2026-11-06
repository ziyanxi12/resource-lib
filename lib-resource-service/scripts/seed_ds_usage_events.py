#!/usr/bin/env python3
"""为设计系统打点统计（管理台数据统计页）生成演示事件。

- 近 N 天（默认 30）跨全部未删设计系统生成 view/usage 打点事件
- 人员取自 mock getAccount 的 10 个账号（真实姓名 + 4 级部门），含少量匿名事件
- 结束后把 design_systems.views / usage 列对齐为各自事件总数（双轨一致，覆盖历史演示值）
- 顺带 upsert users 表（统计兜底链与人员搜索可用）

用法：
    venv/bin/python scripts/seed_ds_usage_events.py            # 生成
    venv/bin/python scripts/seed_ds_usage_events.py --clean    # 先清空事件表再生成
"""

import argparse
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func

from app.database import SessionLocal
from app.models.design_system import DesignSystem
from app.models.ds_usage_event import DsUsageEvent
from app.models.user import User
from app.services.user_service import upsert_user

# mock getAccount（mock-api/data.js）同款人员：account → (名字, dept[1..4])
PEOPLE = {
    "h20031134": ("何光光", ["华为", "2012实验室", "UX部", "设计一组"]),
    "l20031135": ("罗唯", ["华为", "2012实验室", "UX部", "设计二组"]),
    "z20041203": ("张三", ["华为", "ICT产品与解决方案", "平台开发部", "前端组"]),
    "l20041204": ("李四", ["华为", "ICT产品与解决方案", "平台开发部", "后端组"]),
    "w20051507": ("王五", ["华为", "数字能源", "系统设计部", "视觉组"]),
    "c20061608": ("陈六", ["华为", "终端云服务", "应用开发部", "质量组"]),
    "z20071709": ("赵七", ["华为", "云核心网", "架构部", "平台组"]),
    "s20081810": ("孙八", ["华为", "海思半导体", "芯片设计部", "验证组"]),
    "z20091911": ("周九", ["华为", "数据存储与机器视觉", "产品部", "运营组"]),
    "w20102012": ("吴十", ["华为", "数字金融", "解决方案部", "交付组"]),
}
ACCOUNTS = list(PEOPLE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--clean", action="store_true", help="先清空 ds_usage_events 再生成")
    args = ap.parse_args()

    rng = random.Random(42)  # 固定种子：可复现的演示数据
    db = SessionLocal()
    try:
        if args.clean:
            n = db.query(DsUsageEvent).delete()
            db.commit()
            print("已清空事件表：%d 行" % n)

        systems = db.query(DesignSystem.slug, DesignSystem.name).filter(DesignSystem.is_deleted == 0).all()
        if not systems:
            print("没有未删除的设计系统，先在管理台上传至少一个")
            return

        # upsert users 表（兜底链/人员搜索可用）
        for acc, (nick, dept) in PEOPLE.items():
            upsert_user(db, {"account": acc, "nickName": nick, "dept": dept})
        db.commit()

        day0 = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        total = 0
        for d in range(args.days - 1, -1, -1):
            base = day0 - timedelta(days=d)
            weekday = base.weekday()
            weekend_factor = 0.3 if weekday >= 5 else 1.0          # 周末打点少
            ramp = 0.5 + 0.5 * (args.days - d) / args.days         # 越近越多
            # 今天只生成「过去」的时刻（避免最近调用时间显示未来时间）；午夜 0 点刚过则跳过今天
            if d == 0:
                now_h = datetime.now().hour
                if now_h < 1:
                    continue
                lo_h, hi_h = min(8, now_h), now_h
            else:
                lo_h, hi_h = 8, 21

            def rand_when():
                return base + timedelta(hours=rng.randint(lo_h, hi_h), minutes=rng.randint(0, 59))

            for idx, (slug, _) in enumerate(systems):
                popularity = 1.0 + 0.4 * ((idx * 7) % 3)          # 不同系统热度不同
                n_views = int(rng.gauss(6 * weekend_factor * ramp * popularity, 2.5))
                n_usage = int(rng.gauss(2 * weekend_factor * ramp * popularity, 1.2))
                for _ in range(max(0, n_views)):
                    acc = rng.choice(ACCOUNTS)
                    nick, dept = PEOPLE[acc]
                    when = rand_when()
                    dept4 = (dept[1:5] + ["", "", "", ""])[:4]  # dept[0]=公司名不进快照（同 snapshot_fields 口径）
                    db.add(DsUsageEvent(slug=slug, event_type="view", account=acc,
                                        nick_name=nick, dept1=dept4[0] or None,
                                        dept2=dept4[1] or None, dept3=dept4[2] or None,
                                        dept4=dept4[3] or None, created_at=when))
                    total += 1
                for _ in range(max(0, n_usage)):
                    # 少数匿名调用（不带 X-User-Data 的调用方）
                    if rng.random() < 0.12:
                        db.add(DsUsageEvent(slug=slug, event_type="usage", account=None, created_at=rand_when()))
                    else:
                        acc = rng.choice(ACCOUNTS)
                        nick, dept = PEOPLE[acc]
                        when = rand_when()
                        dept4 = (dept[1:5] + ["", "", "", ""])[:4]  # dept[0]=公司名不进快照（同 snapshot_fields 口径）
                        db.add(DsUsageEvent(slug=slug, event_type="usage", account=acc,
                                            nick_name=nick, dept1=dept4[0] or None,
                                            dept2=dept4[1] or None, dept3=dept4[2] or None,
                                            dept4=dept4[3] or None, created_at=when))
                    total += 1
        db.commit()

        # 双轨一致：列值对齐事件总数（覆盖此前手工测试累积的零散计数）
        for slug, _ in systems:
            views = db.query(func.count(DsUsageEvent.id)).filter(
                DsUsageEvent.slug == slug, DsUsageEvent.event_type == "view").scalar() or 0
            usage = db.query(func.count(DsUsageEvent.id)).filter(
                DsUsageEvent.slug == slug, DsUsageEvent.event_type == "usage").scalar() or 0
            db.query(DesignSystem).filter(DesignSystem.slug == slug).update(
                {"views": views, "usage": usage}, synchronize_session=False)
        db.commit()

        print("已生成 %d 条打点事件（近 %d 天 × %d 个系统）" % (total, args.days, len(systems)))
        print("users 表已 upsert %d 人；views/usage 列已对齐事件总数" % len(PEOPLE))
        for slug, name in systems:
            row = db.query(DesignSystem).filter(DesignSystem.slug == slug).one()
            print("  %s（%s）：views=%d usage=%d" % (slug, name, row.views, row.usage))
    finally:
        db.close()


if __name__ == "__main__":
    main()
