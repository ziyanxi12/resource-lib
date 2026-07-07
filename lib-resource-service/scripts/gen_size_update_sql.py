#!/usr/bin/env python3
"""
从变体宽高 JSON 生成 MySQL 批量更新语句，更新 resources 主表的 width/height。

JSON 格式：
[
  {"key": "f88483c3510885a0...", "name": "...", "width": 72, "height": 22},
  ...
]

key 即 component_variants.variant_key，按 variant_key 关联更新。

生成的 SQL 用派生表 JOIN 一次更新一批（默认 500 条/语句），不逐条 UPDATE。

用法：
    python3 gen_size_update_sql.py variants.json                 # 输出到 stdout
    python3 gen_size_update_sql.py variants.json -o update.sql   # 输出到文件
    python3 gen_size_update_sql.py variants.json --batch-size 1000
"""

import argparse
import json
import sys


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "''")


def fmt_num(v) -> str:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"宽高必须是数字，实际是: {v!r}")
    return repr(v)


def build_statement(batch: list) -> str:
    rows = []
    for item in batch:
        vkey = esc(item["key"])
        rows.append(f"SELECT '{vkey}' AS vkey, {fmt_num(item['width'])} AS w, {fmt_num(item['height'])} AS h")
    derived = "\n  UNION ALL ".join(rows)
    return (
        "UPDATE resources r\n"
        "JOIN component_variants cv ON cv.resource_id = r.id\n"
        "JOIN (\n"
        f"  {derived}\n"
        ") t ON t.vkey = cv.variant_key\n"
        "SET r.width = t.w, r.height = t.h;"
    )


def main():
    parser = argparse.ArgumentParser(description="生成 resources 宽高批量更新 SQL")
    parser.add_argument("json_file", help="变体宽高 JSON 文件路径")
    parser.add_argument("-o", "--output", help="输出 SQL 文件路径，缺省输出到 stdout")
    parser.add_argument("--batch-size", type=int, default=500, help="每条 UPDATE 语句包含的变体数，默认 500")
    args = parser.parse_args()

    with open(args.json_file, encoding="utf-8") as f:
        items = json.load(f)

    if not isinstance(items, list):
        sys.exit("JSON 顶层必须是数组")

    valid, skipped = [], 0
    for item in items:
        if item.get("key") and item.get("width") is not None and item.get("height") is not None:
            valid.append(item)
        else:
            skipped += 1
            print(f"跳过缺字段的条目: {item}", file=sys.stderr)

    statements = [
        build_statement(valid[i:i + args.batch_size])
        for i in range(0, len(valid), args.batch_size)
    ]
    sql = "\n\n".join(statements) + "\n"

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(sql)
        print(f"共 {len(valid)} 条变体（跳过 {skipped} 条），生成 {len(statements)} 条 UPDATE 语句 → {args.output}", file=sys.stderr)
    else:
        print(sql)


if __name__ == "__main__":
    main()
