#!/usr/bin/env python3
"""
超大 ZIP 测试包生成脚本（直接写文件，不占内存）

生成 2 个超大包：
  test-2gb.zip      — 100 × 20MB = ~1.95GB，正常大包导入测试
  test-2gb-plus.zip — 110 × 20MB = ~2.15GB，超过旧 2GB 限制，验证后端不拒绝

每个 20MB 文件用 os.urandom 生成随机数据（不可压缩），
ZIP_STORED 模式直接存储（随机数据压缩无意义）。

用法：
  python3 generate_huge_zips.py [输出目录]
"""

import os
import sys
import json
import struct
import zlib
import zipfile

OUTPUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "./test_zips"
FILE_SIZE = 20 * 1024 * 1024  # 20MB per file


def make_minimal_png(width=1, height=1, rgba=(22, 119, 255, 255)):
    """生成最小有效 PNG"""
    def make_chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw = b"\x00" + bytes(rgba) * width
    compressed = zlib.compress(raw)
    return signature + make_chunk(b"IHDR", ihdr) + make_chunk(b"IDAT", compressed) + make_chunk(b"IEND", b"")


def make_data_item(name, file_path, thumbnail_path, idx, group):
    return {
        "name": name,
        "file_name": f"file_{idx}.bin",
        "file_path": file_path,
        "thumbnail_path": thumbnail_path,
        "description": f"超大包测试第 {idx} 条资源，20MB 随机数据",
        "tags": ["超大", "压测", f"g{group}"],
        "search_text": f"huge stress {idx} group {group}",
        "width": 64,
        "height": 64,
        "raw_data": {"index": idx, "group": group, "file_size_mb": 20},
    }


def generate_huge_zip(filepath, num_resources, label_prefix):
    """
    生成超大 ZIP，直接写文件流。
    num_resources: 资源总数
    每个资源含 1 个 20MB 随机文件 + 1 个小 PNG 缩略图
    """
    num_groups = 10
    per_group = num_resources // num_groups
    remainder = num_resources % num_groups

    group_list = []
    idx = 0
    for g in range(num_groups):
        count = per_group + (1 if g < remainder else 0)
        g_data = []
        for j in range(count):
            g_data.append(make_data_item(
                name=f"{label_prefix}-{idx:04d}",
                file_path=f"data/g{g}/file_{idx}.bin",
                thumbnail_path=f"image/g{g}/thumb_{idx}.png",
                idx=idx,
                group=g,
            ))
            idx += 1
        group_list.append({"label": f"超大分组-{g:02d}", "data": g_data})

    config = {"group": group_list}

    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

    # 用 ZIP_STORED 直接存储，随机数据不可压缩
    with zipfile.ZipFile(filepath, "w", zipfile.ZIP_STORED) as zf:
        # 先写 config.json
        zf.writestr("config.json", json.dumps(config, ensure_ascii=False, indent=2))

        # 流式写大文件：分块写入避免单次 20MB 内存峰值
        chunk_size = 4 * 1024 * 1024  # 4MB per chunk
        thumb_png = make_minimal_png(1, 1)

        idx = 0
        for g in range(num_groups):
            count = per_group + (1 if g < remainder else 0)
            for j in range(count):
                file_path = f"data/g{g}/file_{idx}.bin"
                thumb_path = f"image/g{g}/thumb_{idx}.png"

                # 流式写大文件
                with zf.open(file_path, "w") as f_out:
                    written = 0
                    while written < FILE_SIZE:
                        remaining = FILE_SIZE - written
                        size = min(chunk_size, remaining)
                        f_out.write(os.urandom(size))
                        written += size

                # 写小缩略图
                zf.writestr(thumb_path, thumb_png)

                idx += 1

                if idx % 10 == 0:
                    print(f"    已写入 {idx}/{num_resources} 个文件...")

    zip_size = os.path.getsize(filepath)
    print(f"  生成完成: {filepath}")
    print(f"    大小: {zip_size / 1024 / 1024 / 1024:.2f} GB ({zip_size / 1024 / 1024:.0f} MB)")
    print(f"    资源数: {num_resources}")
    print(f"    分组数: {num_groups}")
    print(f"    文件数: {num_resources * 2 + 1}（20MB×N + PNG×N + config.json）")
    return zip_size


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"输出目录: {os.path.abspath(OUTPUT_DIR)}")
    print(f"单文件大小: {FILE_SIZE / 1024 / 1024} MB")
    print()

    print("[1/2] 生成 test-2gb.zip (100 × 20MB ≈ 1.95GB)...")
    size1 = generate_huge_zip(
        os.path.join(OUTPUT_DIR, "test-2gb.zip"),
        num_resources=100,
        label_prefix="资源",
    )

    print()
    print("[2/2] 生成 test-2gb-plus.zip (110 × 20MB ≈ 2.15GB)...")
    size2 = generate_huge_zip(
        os.path.join(OUTPUT_DIR, "test-2gb-plus.zip"),
        num_resources=110,
        label_prefix="超限资源",
    )

    print()
    print("=" * 60)
    print("超大测试包生成完成！")
    print("=" * 60)
    print(f"  test-2gb.zip       — {size1 / 1024 / 1024 / 1024:.2f} GB (100 条资源)")
    print(f"  test-2gb-plus.zip  — {size2 / 1024 / 1024 / 1024:.2f} GB (110 条资源)")
    print()
    print("测试说明：")
    print("  test-2gb.zip       — 正常大包导入测试（1.95GB）")
    print("  test-2gb-plus.zip  — 超过旧 2GB 限制，验证后端不拒绝（2.15GB）")
    print()
    print("⚠ 注意事项：")
    print("  1. 后端 await request.body() 会将整个 ZIP 读入内存，2GB = 2GB RAM 峰值")
    print("  2. 前端 XHR 超时 2 分钟，本地测试建议调大或用 curl 直接测试")
    print("  3. 文件内容为随机二进制，不是合法 SVG/PNG，但 import_service 只做复制不校验格式")
    print("  4. 测试建议用 curl:")
    print('     curl -X POST "http://localhost:8009/api/sources/{id}/import?type=icon" \\')
    print('       -H "Content-Type: application/octet-stream" \\')
    print('       --data-binary @test-2gb.zip')


if __name__ == "__main__":
    main()
