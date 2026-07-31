"""
从历史日志文件导入搜索调用记录到采集表（命令行入口）。

核心逻辑在 app/services/search_stats_service.py 的 import_logs_to_db()，
API 端点 POST /api/search-stats/import-logs 也可触发。

用法：
    cd lib-resource-service && python3 scripts/import_search_logs.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.services.search_stats_service import import_logs_to_db

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        result = import_logs_to_db(db)
        print(f"扫描日志文件: {result['files_scanned']} 个")
        print(f"解析搜索请求: {result['total_requests']} 条")
        print(f"  - 成功: {result['success']} 条")
        print(f"  - 失败: {result['error']} 条")
        print(f"写入主表: {result['main_inserted']} 行")
        print(f"写入结果子表: {result['results_inserted']} 行 (仅前3条/次)")
        print("\n导入完成。请手动调用 POST /api/search-stats/refresh 刷新看板数据。")
    finally:
        db.close()
