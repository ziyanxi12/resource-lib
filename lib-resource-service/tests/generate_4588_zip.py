#!/usr/bin/env python3
"""
生成 4588 条资源的压测 ZIP 包（复现 Phase 2 逐条 flush 性能 bug）

每条资源含 1 个最小 SVG + 1 个 1x1 PNG 缩略图。
ZIP 内文件数 = 4588 × 2 + 1(config) = 9177

分组结构：10 个一级分组 × 2 个子分组 = 20 个叶子分组 + 10 个父分组 = 30 个分组节点
资源均匀分布在 20 个叶子分组中（每组 ~229 条）
"""

import io
import json
import struct
import sys
import zipfile
import zlib

OUTPUT = sys.argv[1] if len(sys.argv) > 1 else "./test_zips/test-4588.zip"
TOTAL_RESOURCES = 4588
NUM_TOP_GROUPS = 10
CHILDREN_PER_TOP = 2
NUM_LEAF_GROUPS = NUM_TOP_GROUPS * CHILDREN_PER_TOP  # 20
PER_LEAF = TOTAL_RESOURCES // NUM_LEAF_GROUPS          # 229
REMAINDER = TOTAL_RESOURCES - PER_LEAF * NUM_LEAF_GROUPS  # 8

SVG_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">'
    '<rect width="24" height="24" rx="4" fill="#1677ff"/>'
    '<text x="12" y="16" font-size="10" text-anchor="middle" fill="white">{}</text>'
    '</svg>'
)


def make_minimal_png():
    """生成 1x1 RGBA PNG（~67 bytes）"""
    def chunk(ctype, data):
        c = ctype + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    raw = b"\x00\x00\x00\x00\x00"
    idat = zlib.compress(raw)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def main():
    import os
    os.makedirs(os.path.dirname(OUTPUT) or ".", exist_ok=True)

    png_bytes = make_minimal_png()
    buf = io.BytesIO()
    zf = zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED)

    group_list = []
    idx = 0
    for g in range(NUM_TOP_GROUPS):
        children = []
        for c in range(CHILDREN_PER_TOP):
            leaf_idx = g * CHILDREN_PER_TOP + c
            count = PER_LEAF + (1 if leaf_idx < REMAINDER else 0)
            data_items = []
            for j in range(count):
                svg_path = f"data/g{g}/c{c}/item_{idx}.svg"
                thumb_path = f"image/g{g}/c{c}/thumb_{idx}.png"

                zf.writestr(svg_path, SVG_TEMPLATE.format(str(idx)[-1]).encode())
                zf.writestr(thumb_path, png_bytes)

                data_items.append({
                    "name": f"图标-{idx:04d}",
                    "file_name": f"item_{idx}.svg",
                    "file_path": svg_path,
                    "thumbnail_path": thumb_path,
                    "description": f"压测资源第 {idx} 条",
                    "tags": ["压测", f"g{g}", f"c{c}"],
                    "search_text": f"stress test {idx} group {g} child {c}",
                    "width": 24,
                    "height": 24,
                    "raw_data": {"index": idx, "group": g, "child": c},
                })
                idx += 1

            children.append({
                "label": f"子分组-{g:02d}-{c}",
                "data": data_items,
            })

        group_list.append({
            "label": f"一级分组-{g:02d}",
            "data": [],
            "children": children,
        })

    config = {"group": group_list}
    zf.writestr("config.json", json.dumps(config, ensure_ascii=False))
    zf.close()

    with open(OUTPUT, "wb") as f:
        f.write(buf.getvalue())

    size_mb = os.path.getsize(OUTPUT) / 1024 / 1024
    print(f"生成完成: {OUTPUT}")
    print(f"  ZIP 大小: {size_mb:.2f} MB")
    print(f"  资源数: {TOTAL_RESOURCES}")
    print(f"  分组数: {NUM_TOP_GROUPS + NUM_LEAF_GROUPS} ({NUM_TOP_GROUPS} 父 + {NUM_LEAF_GROUPS} 叶)")
    print(f"  ZIP 内文件数: {TOTAL_RESOURCES * 2 + 1} (SVG×{TOTAL_RESOURCES} + PNG×{TOTAL_RESOURCES} + config.json)")
    print(f"  Phase 1 flat_items = {TOTAL_RESOURCES} (复现 4588 次 flush)")
    print()
    print("测试命令:")
    print('  curl -X POST "http://localhost:8009/api/sources/{id}/import?type=icon" \\')
    print(f'    -H "Content-Type: application/octet-stream" \\')
    print(f'    --data-binary @{OUTPUT} --max-time 600')


if __name__ == "__main__":
    main()
