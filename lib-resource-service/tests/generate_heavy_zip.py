#!/usr/bin/env python3
"""
生成大内存压测包（二进制密集型）

test-heavy.zip — 200 条资源，每条含 256x256 PNG（~200KB）
  解压后 ~80MB，ZIP ~40MB，真正测试内存和 I/O
"""

import os
import sys
import json
import zipfile
import struct
import zlib
import io

OUTPUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "./test_zips"


def make_gradient_png(width=256, height=256):
    """生成渐变 PNG，体积较大（~200KB 未压缩）"""
    def make_chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)

    raw = b""
    for y in range(height):
        raw += b"\x00"
        for x in range(width):
            r = (x * 255) // width
            g = (y * 255) // height
            b = ((x + y) * 255) // (width + height)
            raw += bytes([r, g, b, 255])

    compressed = zlib.compress(raw, 6)
    return signature + make_chunk(b"IHDR", ihdr) + make_chunk(b"IDAT", compressed) + make_chunk(b"IEND", b"")


def make_svg_with_paths(count=100, size=64):
    """生成含多条 path 的 SVG"""
    paths = ""
    for i in range(count):
        x1 = i % size
        y1 = (i * 3) % size
        x2 = (i * 7) % size
        y2 = (i * 11) % size
        paths += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="hsl({i*3%360},70%,50%)" stroke-width="1"/>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">{paths}</svg>'.encode("utf-8")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, "test-heavy.zip")

    buf = io.BytesIO()
    zf = zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED)

    total = 200
    per_group = 20
    num_groups = total // per_group

    print(f"生成大内存压测包: {total} 条资源, {num_groups} 个分组")
    print(f"每条资源含 256x256 渐变 PNG (~200KB) + 多 path SVG")

    group_list = []
    idx = 0
    for g in range(num_groups):
        g_data = []
        for j in range(per_group):
            svg_path = f"data/g{g}/item_{idx}.svg"
            thumb_path = f"image/g{g}/thumb_{idx}.png"

            zf.writestr(svg_path, make_svg_with_paths(80, 64))
            zf.writestr(thumb_path, make_gradient_png(256, 256))

            g_data.append({
                "name": f"压测资源-{idx:04d}",
                "file_name": f"item_{idx}.svg",
                "file_path": svg_path,
                "thumbnail_path": thumb_path,
                "description": f"大内存压测第 {idx} 条，含 256x256 渐变缩略图",
                "tags": ["压测", "大内存", f"g{g}"],
                "search_text": f"stress heavy {idx} group {g}",
                "width": 64,
                "height": 64,
                "raw_data": {"index": idx, "group": g, "type": "heavy"},
            })
            idx += 1

        group_list.append({
            "label": f"压测分组-{g:02d}",
            "data": g_data,
            "children": [
                {"label": f"子分组-{g}-A", "data": []},
            ],
        })

    config = {"group": group_list}
    zf.writestr("config.json", json.dumps(config, ensure_ascii=False, indent=2))
    zf.close()

    with open(filepath, "wb") as f:
        f.write(buf.getvalue())

    zip_size = os.path.getsize(filepath) / 1024 / 1024
    total_groups = num_groups * 2
    print(f"\n生成完成: {filepath}")
    print(f"  ZIP 大小: {zip_size:.2f} MB")
    print(f"  分组数: {total_groups}")
    print(f"  资源数: {total}")
    print(f"  文件数: {total * 2 + 1}（SVG + PNG + config.json）")

    # 估算解压后大小
    print(f"  解压后估算: ~{total * 0.2:.0f} MB（200KB × {total} PNG）")


if __name__ == "__main__":
    main()
