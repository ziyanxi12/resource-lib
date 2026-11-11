"""DESIGN.md（octo-design-md/1 格式）→ design-system.json 解析服务。

移植自 design-system-demo/script/extract_design_md.py，输入输出契约不变：
- 输入：MD 文本（YAML frontmatter + `## 章节 {#anchor}` 正文 + ```json design 代码块）
- 输出：design-system.json 同构 dict（id/name/cover/overview/
  color/typography/spacing/radius/shadow/coverage/meta）。

**尽力提取，永不抛错**（DESIGN.md 内容不做任何校验）：
- frontmatter 缺失/损坏 → 元数据降级为空 dict，章节数据照常提取
- 某章节 json design 代码块 JSON 非法 → 跳过该章节（warning 日志），其余章节保留
- 完全不可解码（非 UTF-8）由调用方（design_system_zip.parse_md_root）降级为空 dict

注意：parse_frontmatter 本身仍抛 ValueError——skill 附件（SKILL.md）的严格校验
（design_system_zip.extract_skill_name）依赖它，勿改。
"""

import json
import logging
import re
from collections import OrderedDict
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# 展示端第一期支持的 token 区块（组件 / 资产 / 布局 Pattern 不在解析范围）
SECTION_ANCHORS = ["color", "typography", "spacing", "radius", "shadow"]
COVERAGE_KEYS = ["overview", "color", "typography", "spacing", "radius", "shadow"]


def parse_frontmatter(text: str) -> "OrderedDict[str, object]":
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        raise ValueError("缺少 frontmatter（--- ... --- 头部块，octo-design-md/1 格式）")
    fm = OrderedDict()
    for line in m.group(1).split("\n"):
        mm = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not mm:
            continue
        k, v = mm.group(1), mm.group(2).strip()
        if len(v) >= 2 and v[0] in "\"'" and v[-1] == v[0]:
            v = v[1:-1]
        elif re.match(r"^-?\d+$", v):
            v = int(v)
        fm[k] = v
    return fm


def split_sections(text: str) -> "OrderedDict[str, str]":
    """按 `## 标题 {#anchor}` 切分，返回 OrderedDict(anchor → 章节文本)"""
    marks = []
    for m in re.finditer(r"^## .+? \{#(\w+)\}\s*$", text, re.MULTILINE):
        marks.append((m.group(1), m.start()))
    out = OrderedDict()
    for i, (anchor, start) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(text)
        out[anchor] = text[start:end]
    return out


def first_paragraph(section_text: str) -> str:
    """章节正文第一段（跳过标题 / 引用块 / 代码块 / 子标题）"""
    body = section_text.split("\n", 1)[1] if "\n" in section_text else ""
    lines = []
    for line in body.split("\n"):
        s = line.strip()
        if not lines:
            if not s or s.startswith(">") or s.startswith("#") or s.startswith("```"):
                continue
        else:
            if not s:  # 段落结束
                break
            if s.startswith(">") or s.startswith("#") or s.startswith("```"):
                break
        lines.append(s)
    return "".join(lines)


def design_block(section_text: str, anchor: str) -> Optional[dict]:
    """提取章节内第一个 ```json design 代码块并解析"""
    m = re.search(r"```json design\n([\s\S]*?)\n```", section_text)
    if not m:
        return None
    try:
        return json.loads(m.group(1), object_pairs_hook=OrderedDict)
    except ValueError as e:
        raise ValueError("章节「%s」的 json design 代码块 JSON 解析失败：%s" % (anchor, e))


def rule_list(section_text: str) -> List[str]:
    """「### 使用规则」下的 `- ` 列表；无则空数组"""
    m = re.search(r"###\s*使用规则\s*\n((?:\n|- .+\n?)+)", section_text)
    if not m:
        return []
    return [l[2:].strip() for l in m.group(1).split("\n") if l.startswith("- ")]


def bullet_list(section_text: str, after_heading: str) -> List[str]:
    """指定子标题下的 `- ` 列表（用于设计原则等）"""
    m = re.search(
        r"###\s*" + re.escape(after_heading) + r"\s*\n([\s\S]*?)(?=\n###|\n```|\Z)",
        section_text,
    )
    if not m:
        return []
    return [l[2:].strip() for l in m.group(1).split("\n") if l.startswith("- ")]


def blockquote_source(section_text: str, after_heading: str) -> str:
    """指定子标题下的 `> 来源：...` 引用行"""
    m = re.search(r"###\s*" + re.escape(after_heading) + r"\s*\n\s*>\s*(.+)", section_text)
    return m.group(1).strip() if m else ""


def doc_note(text: str) -> str:
    """文档级引用块（frontmatter 之后、第一个 `## ` 之前的 `>` 段）"""
    head = re.match(r"^---\n.*?\n---\n(.*?)^## ", text, re.DOTALL | re.MULTILINE)
    if not head:
        return ""
    lines = [l.lstrip("> ").strip() for l in head.group(1).split("\n") if l.startswith(">")]
    return " ".join(lines)


def parse_md(md_text: str) -> Dict:
    """DESIGN.md（octo-design-md/1）→ design-system.json 同构 dict（尽力提取，永不抛错）。

    - frontmatter 缺失/损坏 → 元数据全空（id/name/cover/…），章节数据照常提取
    - 章节 json design 代码块 JSON 非法 → 跳过该章节（warning），其余章节保留
    """
    try:
        fm = parse_frontmatter(md_text)
    except ValueError as e:
        logger.warning("[zip-import] DESIGN.md frontmatter 缺失/损坏（元数据降级为空）：%s", e)
        fm = OrderedDict()
    sections = split_sections(md_text)

    def sec_with_meta(anchor: str) -> Optional[dict]:
        st = sections[anchor]
        block = design_block(st, anchor)
        if block is None:
            return None
        block["desc"] = first_paragraph(st)
        block["rules"] = rule_list(st)
        return block

    out = OrderedDict()

    # ── 顶层（以 MD frontmatter 为准）──
    out["id"] = fm.get("id", "")
    out["name"] = fm.get("name", "")
    out["source"] = {"skill": fm.get("source_skill", ""), "adapter": fm.get("adapter", "")}
    out["cover"] = fm.get("cover", "")

    # ── 概览：正文段落 + 设计原则 ──
    ov = sections.get("overview", "")
    out["overview"] = {
        "text": first_paragraph(ov),
        "principles": bullet_list(ov, "设计原则"),
        "principlesSource": blockquote_source(ov, "设计原则"),
    }

    # ── 五个 token 区块（组件 / 资产 / 布局 Pattern 不解析）──
    for anchor in SECTION_ANCHORS:
        if anchor in sections:
            try:
                sec = sec_with_meta(anchor)
            except ValueError as e:
                logger.warning("[zip-import] DESIGN.md 章节「%s」JSON 块非法（跳过该章节）：%s", anchor, e)
                continue
            if sec is not None:
                out[anchor] = sec

    # ── coverage：按区块存在性 ──
    coverage = OrderedDict()
    for key in COVERAGE_KEYS:
        coverage[key] = key in out and bool(out[key])
    out["coverage"] = coverage

    # ── meta：frontmatter 其余字段全量保留 ──
    out["meta"] = OrderedDict()
    for k in [
        "format", "author", "usage", "order", "source_skill", "adapter",
        "source_files", "source_size", "source_entry",
    ]:
        if k in fm:
            out["meta"][k] = fm[k]
    out["meta"]["source_file"] = "DESIGN.md"
    out["meta"]["note"] = doc_note(md_text)

    return out
