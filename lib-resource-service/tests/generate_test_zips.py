#!/usr/bin/env python3
"""
全量批量导入测试 ZIP 包生成脚本

生成以下测试包：
1. test-multi-group.zip    — 多分组嵌套（3 层深度，混合 data 和 children）
2. test-external-url.zip   — 全部使用外部链接（无本地文件）
3. test-large.zip          — 大内存（500 条资源 + 500 个 SVG 文件）
4. test-mixed.zip          — 混合场景（本地文件 + 外部链接 + 空分组 + 超长名称）
5. test-empty.zip          — 边界测试（空 group 数组）
6. test-error.zip          — 错误场景（字段缺失、文件不存在、无效 data）

用法：
    python3 generate_test_zips.py [输出目录]
默认输出到 ./test_zips/
"""

import os
import sys
import json
import zipfile
import io
import struct
import zlib
import uuid

OUTPUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "./test_zips"


# ──────────────────────────────────────────────
# 辅助：生成最小 PNG（纯色）
# ──────────────────────────────────────────────
def make_minimal_png(width=1, height=1, rgba=(255, 0, 0, 255)):
    """生成最小有效 PNG 文件 bytes"""
    def make_chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw = b""
    for _ in range(height):
        raw += b"\x00" + bytes(rgba[:3] + (rgba[3],)) * width
    compressed = zlib.compress(raw)
    return signature + make_chunk(b"IHDR", ihdr) + make_chunk(b"IDAT", compressed) + make_chunk(b"IEND", b"")


def make_svg(name="icon", color="#1677ff", size=24):
    """生成简单 SVG 文件 bytes"""
    content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <rect width="{size}" height="{size}" rx="4" fill="{color}"/>
  <text x="{size//2}" y="{size//2+5}" font-size="10" text-anchor="middle" fill="white">{name[0].upper()}</text>
</svg>'''
    return content.encode("utf-8")


def make_thumbnail(label="T", color=(22, 119, 255)):
    """生成带字母的 48x48 PNG 缩略图"""
    return make_minimal_png(48, 48, color + (255,))


# ──────────────────────────────────────────────
# ZIP 构建器
# ──────────────────────────────────────────────
class ZipBuilder:
    def __init__(self):
        self.buf = io.BytesIO()
        self.zf = zipfile.ZipFile(self.buf, "w", zipfile.ZIP_DEFLATED)
        self.file_counter = 0

    def add_config(self, config: dict):
        self.zf.writestr("config.json", json.dumps(config, ensure_ascii=False, indent=2))

    def add_svg(self, path: str, name="icon", color="#1677ff", size=24):
        self.zf.writestr(path, make_svg(name, color, size))

    def add_png(self, path: str, label="T", color=(22, 119, 255)):
        self.zf.writestr(path, make_thumbnail(label, color))

    def add_text(self, path: str, content: str):
        self.zf.writestr(path, content)

    def save(self, filepath: str):
        self.zf.close()
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(self.buf.getvalue())
        size_mb = os.path.getsize(filepath) / 1024 / 1024
        print(f"  生成: {filepath} ({size_mb:.2f} MB)")

    @property
    def size(self):
        return self.buf.tell()


def make_data_item(
    name: str,
    file_path: str = None,
    file_url: str = None,
    thumbnail_path: str = None,
    description: str = "",
    tags=None,
    search_text: str = "",
    raw_data=None,
    width=24,
    height=24,
    file_name: str = None,
):
    """构建单个 data 项"""
    item = {
        "name": name,
        "file_name": file_name,
        "description": description,
        "tags": tags or [],
        "search_text": search_text,
        "raw_data": raw_data or {},
        "width": width,
        "height": height,
    }
    if file_path:
        item["file_path"] = file_path
    if file_url:
        item["file_url"] = file_url
    if thumbnail_path:
        item["thumbnail_path"] = thumbnail_path
    return item


# ──────────────────────────────────────────────
# 测试包 1：多分组嵌套
# ──────────────────────────────────────────────
def gen_multi_group(output_dir):
    """3 层嵌套分组，每层有 data，叶子节点也有 data"""
    print("\n[1] 生成多分组嵌套测试包...")
    zb = ZipBuilder()

    colors = ["#1677ff", "#52c41a", "#faad14", "#ff4d4f", "#722ed1", "#13c2c2"]

    group_children = []
    for i in range(3):
        child_label = f"二级分组-{i + 1}"
        child_data = []
        for j in range(2):
            svg_path = f"data/{child_label}/icon_{i}_{j}.svg"
            thumb_path = f"image/{child_label}/thumb_{i}_{j}.png"
            item_name = f"图标-{i}-{j}"
            zb.add_svg(svg_path, item_name, colors[(i + j) % len(colors)])
            zb.add_png(thumb_path, item_name)
            child_data.append(make_data_item(
                name=item_name,
                file_name=f"icon_{i}_{j}.svg",
                file_path=svg_path,
                thumbnail_path=thumb_path,
                description=f"二级分组下的第 {j + 1} 个图标",
                tags=["图标", f"组{i + 1}"],
                search_text=f"icon {i} {j}",
                raw_data={"category": "icon", "level": 2},
            ))
        group_children.append({"label": child_label, "data": child_data})

    group_data = []
    for i in range(4):
        svg_path = f"data/level1/icon_{i}.svg"
        thumb_path = f"image/level1/thumb_{i}.png"
        item_name = f"一级图标-{i}"
        zb.add_svg(svg_path, item_name, colors[i % len(colors)], 32)
        zb.add_png(thumb_path, item_name)
        group_data.append(make_data_item(
            name=item_name,
            file_name=f"icon_{i}.svg",
            file_path=svg_path,
            thumbnail_path=thumb_path,
            description=f"一级分组下的第 {i + 1} 个图标",
            tags=["图标", "一级"],
            search_text=f"level1 icon {i}",
            width=32,
            height=32,
            raw_data={"category": "icon", "level": 1},
        ))

    group_list = [
        {
            "label": "图标库-第一层",
            "data": group_data,
            "children": group_children,
        },
        {
            "label": "空分组（无 data 无 children）",
            "data": [],
        },
        {
            "label": "只有 data 的分组",
            "data": [
                make_data_item(
                    name="独立图标",
                    file_name="standalone.svg",
                    file_path="data/standalone/standalone.svg",
                    thumbnail_path="image/standalone/thumb.png",
                    description="独立分组下的图标",
                    tags=["独立"],
                    search_text="standalone",
                ),
            ],
        },
    ]

    zb.add_svg("data/standalone/standalone.svg", "S", "#ff4d4f")
    zb.add_png("image/standalone/thumb.png", "S")

    config = {"group": group_list}
    zb.add_config(config)
    zb.save(os.path.join(output_dir, "test-multi-group.zip"))


# ──────────────────────────────────────────────
# 测试包 2：全部外部链接
# ──────────────────────────────────────────────
def gen_external_url(output_dir):
    """全部使用 file_url，ZIP 内只有 config.json，无资源文件"""
    print("\n[2] 生成外部链接测试包...")
    zb = ZipBuilder()

    group_data = []
    for i in range(5):
        group_data.append(make_data_item(
            name=f"外部资源-{i}",
            file_name=f"ext_{i}.svg",
            file_url=f"https://cdn.example.com/icons/ext_{i}.svg",
            thumbnail_path=None,
            description=f"使用外部链接的资源 {i}",
            tags=["外部", "url"],
            search_text=f"external url {i}",
            raw_data={"source": "cdn"},
        ))

    child_data = []
    for i in range(3):
        child_data.append(make_data_item(
            name=f"子外部资源-{i}",
            file_name=f"child_ext_{i}.svg",
            file_url=f"https://cdn.example.com/child/{i}.svg",
            thumbnail_path=None,
            description=f"子分组外部链接资源 {i}",
            tags=["外部", "子级"],
            search_text=f"child external {i}",
        ))

    config = {
        "group": [
            {
                "label": "外部链接分组",
                "data": group_data,
                "children": [
                    {"label": "外部链接子分组", "data": child_data},
                ],
            },
        ]
    }
    zb.add_config(config)
    zb.save(os.path.join(output_dir, "test-external-url.zip"))


# ──────────────────────────────────────────────
# 测试包 3：大内存（大量资源 + 大量文件）
# ──────────────────────────────────────────────
def gen_large(output_dir):
    """500 条资源 + 500 个 SVG + 500 个 PNG，多分组"""
    print("\n[3] 生成大内存测试包（500 条资源）...")
    zb = ZipBuilder()

    total = 500
    per_group = 50
    num_groups = total // per_group  # 10 个一级分组

    colors = ["#1677ff", "#52c41a", "#faad14", "#ff4d4f", "#722ed1",
              "#13c2c2", "#eb2f96", "#fa8c16", "#a0d911", "#2f54eb"]

    group_list = []
    idx = 0
    for g in range(num_groups):
        g_data = []
        for j in range(per_group):
            svg_path = f"data/group_{g}/item_{idx}.svg"
            thumb_path = f"image/group_{g}/thumb_{idx}.png"
            name = f"资源-{idx:04d}"
            zb.add_svg(svg_path, name, colors[g % len(colors)], 48)
            zb.add_png(thumb_path, name)
            g_data.append(make_data_item(
                name=name,
                file_name=f"item_{idx}.svg",
                file_path=svg_path,
                thumbnail_path=thumb_path,
                description=f"大内存测试第 {idx} 条资源，属于分组 {g}",
                tags=["大内存", "压测", f"g{g}"],
                search_text=f"stress test item {idx} group {g}",
                width=48,
                height=48,
                raw_data={"index": idx, "group": g, "batch": "large"},
            ))
            idx += 1

        child_data = []
        for j in range(10):
            c_idx = idx
            idx += 1
            svg_path = f"data/group_{g}/child/item_{c_idx}.svg"
            thumb_path = f"image/group_{g}/child/thumb_{c_idx}.png"
            name = f"子资源-{c_idx:04d}"
            zb.add_svg(svg_path, name, colors[(g + 1) % len(colors)], 24)
            zb.add_png(thumb_path, name)
            child_data.append(make_data_item(
                name=name,
                file_name=f"item_{c_idx}.svg",
                file_path=svg_path,
                thumbnail_path=thumb_path,
                description=f"子分组资源 {c_idx}",
                tags=["子级", "大内存"],
                search_text=f"child {c_idx}",
                raw_data={"index": c_idx, "parent_group": g},
            ))

        group_list.append({
            "label": f"压测分组-{g:02d}",
            "data": g_data,
            "children": [
                {"label": f"子分组-{g:02d}-A", "data": child_data},
                {"label": f"子分组-{g:02d}-B", "data": []},
            ],
        })

    config = {"group": group_list}
    zb.add_config(config)
    zb.save(os.path.join(output_dir, "test-large.zip"))

    total_resources = num_groups * (per_group + 10)
    total_groups = num_groups * 3
    print(f"  统计: {total_groups} 个分组, {total_resources} 条资源, "
          f"{total_resources} 个 SVG + {total_resources} 个 PNG")


# ──────────────────────────────────────────────
# 测试包 4：混合场景
# ──────────────────────────────────────────────
def gen_mixed(output_dir):
    """混合：本地文件 + 外部链接 + 空分组 + 无缩略图 + 超长名称"""
    print("\n[4] 生成混合场景测试包...")
    zb = ZipBuilder()

    long_name = "超长分组名称测试" + "A" * 100

    config = {
        "group": [
            {
                "label": "混合分组-本地+外部",
                "data": [
                    make_data_item(
                        name="本地资源",
                        file_name="local.svg",
                        file_path="data/mixed/local.svg",
                        thumbnail_path="image/mixed/local.png",
                        description="使用本地文件",
                        tags=["本地"],
                        search_text="local",
                    ),
                    make_data_item(
                        name="外部资源",
                        file_name="remote.svg",
                        file_url="https://cdn.example.com/mixed/remote.svg",
                        description="使用外部链接",
                        tags=["外部"],
                        search_text="remote",
                    ),
                    make_data_item(
                        name="无缩略图资源",
                        file_name="nothumb.svg",
                        file_path="data/mixed/nothumb.svg",
                        thumbnail_path=None,
                        description="没有缩略图",
                        tags=["无缩略图"],
                    ),
                    make_data_item(
                        name="无标签无描述资源",
                        file_name="minimal.svg",
                        file_path="data/mixed/minimal.svg",
                        thumbnail_path="image/mixed/minimal.png",
                    ),
                ],
                "children": [
                    {"label": "空子分组", "data": []},
                    {
                        "label": "深层嵌套-L2",
                        "data": [],
                        "children": [
                            {
                                "label": "深层嵌套-L3",
                                "data": [
                                    make_data_item(
                                        name="深层资源",
                                        file_name="deep.svg",
                                        file_path="data/mixed/deep/deep.svg",
                                        thumbnail_path="image/mixed/deep/deep.png",
                                        description="第三层分组下的资源",
                                        tags=["深层", "嵌套"],
                                        search_text="deep nested",
                                        raw_data={"depth": 3},
                                    ),
                                ],
                                "children": [
                                    {"label": "深层嵌套-L4", "data": []},
                                ],
                            },
                        ],
                    },
                ],
            },
            {"label": "空分组", "data": []},
            {"label": long_name, "data": []},
            {
                "label": "外部链接无缩略图",
                "data": [
                    make_data_item(
                        name="纯外部-无缩略图",
                        file_name="pure_ext.svg",
                        file_url="https://cdn.example.com/pure.svg",
                        description="纯外部链接无缩略图",
                        tags=["外部", "无缩略图"],
                    ),
                ],
            },
        ]
    }

    zb.add_svg("data/mixed/local.svg", "L", "#1677ff")
    zb.add_png("image/mixed/local.png", "L")
    zb.add_svg("data/mixed/nothumb.svg", "N", "#faad14")
    zb.add_svg("data/mixed/minimal.svg", "M", "#52c41a")
    zb.add_png("image/mixed/minimal.png", "M")
    zb.add_svg("data/mixed/deep/deep.svg", "D", "#ff4d4f")
    zb.add_png("image/mixed/deep/deep.png", "D")

    zb.add_config(config)
    zb.save(os.path.join(output_dir, "test-mixed.zip"))


# ──────────────────────────────────────────────
# 测试包 5：空 group 数组（边界）
# ──────────────────────────────────────────────
def gen_empty(output_dir):
    """空 group 数组，应该导入 0 个分组 0 个资源"""
    print("\n[5] 生成空 group 边界测试包...")
    zb = ZipBuilder()
    zb.add_config({"group": []})
    zb.save(os.path.join(output_dir, "test-empty.zip"))


# ──────────────────────────────────────────────
# 测试包 6：错误场景
# ──────────────────────────────────────────────
def gen_error(output_dir):
    """错误场景：文件不存在、缺少必填字段、data 非 list 等"""
    print("\n[6] 生成错误场景测试包...")
    zb = ZipBuilder()

    config = {
        "group": [
            {
                "label": "正常分组",
                "data": [
                    make_data_item(
                        name="正常资源",
                        file_name="ok.svg",
                        file_path="data/error/ok.svg",
                        thumbnail_path="image/error/ok.png",
                        description="这条应该正常导入",
                        tags=["正常"],
                    ),
                ],
            },
            {
                "label": "错误分组-文件不存在",
                "data": [
                    make_data_item(
                        name="文件不存在",
                        file_name="missing.svg",
                        file_path="data/error/not_exist.svg",
                        thumbnail_path="image/error/ok.png",
                        description="file_path 指向不存在的文件",
                    ),
                    make_data_item(
                        name="缩略图不存在",
                        file_name="ok2.svg",
                        file_path="data/error/ok.svg",
                        thumbnail_path="image/error/not_exist.png",
                        description="thumbnail_path 指向不存在的文件",
                    ),
                    make_data_item(
                        name="无 file_path 无 file_url",
                        file_name="nothing.svg",
                        description="既没有 file_path 也没有 file_url",
                        tags=["错误"],
                    ),
                ],
            },
            {
                "label": "缺少 label 的分组会被跳过",
                "data": [],
            },
        ]
    }
    # 故意把第三个分组的 label 删掉（模拟缺少 label）
    config["group"][2].pop("label")

    zb.add_svg("data/error/ok.svg", "OK", "#52c41a")
    zb.add_png("image/error/ok.png", "OK")
    zb.add_config(config)
    zb.save(os.path.join(output_dir, "test-error.zip"))


# ──────────────────────────────────────────────
# 测试包 7：超大单文件
# ──────────────────────────────────────────────
def gen_large_file(output_dir):
    """包含一个较大的 SVG 文件（~1MB），测试大文件复制"""
    print("\n[7] 生成大单文件测试包...")
    zb = ZipBuilder()

    large_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024">'
    for i in range(2000):
        x = i % 100 * 10
        y = i // 100 * 10
        color = f"#{i % 256:02x}{(i * 3) % 256:02x}{(i * 7) % 256:02x}"
        large_svg += f'<rect x="{x}" y="{y}" width="10" height="10" fill="{color}"/>'
    large_svg += "</svg>"

    config = {
        "group": [
            {
                "label": "大文件分组",
                "data": [
                    make_data_item(
                        name="大尺寸SVG",
                        file_name="large.svg",
                        file_path="data/large/large.svg",
                        thumbnail_path="image/large/thumb.png",
                        description="包含 2000 个 rect 的大 SVG 文件",
                        tags=["大文件", "压测"],
                        search_text="large svg stress",
                        width=1024,
                        height=1024,
                        raw_data={"rect_count": 2000},
                    ),
                    make_data_item(
                        name="大文件2",
                        file_name="large2.svg",
                        file_path="data/large/large2.svg",
                        thumbnail_path="image/large/thumb2.png",
                        description="第二个大 SVG",
                        tags=["大文件"],
                        width=1024,
                        height=1024,
                    ),
                ],
            },
        ]
    }

    zb.add_text("data/large/large.svg", large_svg)
    zb.add_text("data/large/large2.svg", large_svg)
    zb.add_png("image/large/thumb.png", "L1")
    zb.add_png("image/large/thumb2.png", "L2")
    zb.add_config(config)
    zb.save(os.path.join(output_dir, "test-large-file.zip"))


# ──────────────────────────────────────────────
# 主函数
# ──────────────────────────────────────────────
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"输出目录: {os.path.abspath(OUTPUT_DIR)}")

    gen_multi_group(OUTPUT_DIR)
    gen_external_url(OUTPUT_DIR)
    gen_large(OUTPUT_DIR)
    gen_mixed(OUTPUT_DIR)
    gen_empty(OUTPUT_DIR)
    gen_error(OUTPUT_DIR)
    gen_large_file(OUTPUT_DIR)

    print("\n" + "=" * 60)
    print("全部测试包生成完成！")
    print("=" * 60)

    files = sorted(f for f in os.listdir(OUTPUT_DIR) if f.endswith(".zip"))
    total_size = 0
    for f in files:
        size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
        total_size += size
        print(f"  {f:40s}  {size / 1024 / 1024:8.2f} MB")
    print(f"  {'总计':40s}  {total_size / 1024 / 1024:8.2f} MB")
    print()

    print("测试包说明：")
    print("  test-multi-group.zip   — 多分组嵌套（3层），混合 data/children/空分组")
    print("  test-external-url.zip  — 全部外部链接（file_url），ZIP 内无资源文件")
    print("  test-large.zip         — 大内存压测（500条资源 + 1000个文件）")
    print("  test-mixed.zip         — 混合场景（本地+外部+无缩略图+深层嵌套+超长名称）")
    print("  test-empty.zip         — 边界测试（空 group 数组）")
    print("  test-error.zip         — 错误场景（文件不存在/缺字段/缺label）")
    print("  test-large-file.zip    — 大单文件（~1MB SVG × 2）")


if __name__ == "__main__":
    main()
