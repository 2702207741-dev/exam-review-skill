"""
Markdown 解析器

识别 # 标题层级、**加粗**、==高亮== 等 Markdown 标记。
"""

from __future__ import annotations

import re

from .models import ParsedDocument


def parse_md(file_path: str, priority: str = "normal") -> ParsedDocument:
    """解析 Markdown 文件，返回 ParsedDocument"""
    doc = ParsedDocument(
        file_path=file_path,
        file_type="md",
        priority=priority,
    )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="gbk") as f:
                content = f.read()
        except Exception as e:
            doc.parse_errors.append(f"无法读取 MD 文件: {e}")
            return doc
    except Exception as e:
        doc.parse_errors.append(f"无法打开 MD 文件: {e}")
        return doc

    if not content.strip():
        doc.parse_errors.append("文件内容为空")
        return doc

    lines = content.split("\n")
    doc.total_pages = 1

    in_code_block = False

    for line in lines:
        stripped = line.strip()

        # 跳过代码块
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # 跳过空行和分隔线
        if not stripped or stripped.startswith("---") or stripped.startswith("==="):
            continue

        # 标题识别
        level = _get_heading_level(stripped)
        plain_text = _strip_markdown(stripped)
        is_important = _has_emphasis(stripped)

        if plain_text:
            doc.add_paragraph(
                plain_text,
                level=level,
                is_important=is_important,
            )

    return doc


def _get_heading_level(line: str) -> int:
    """识别 # 标题层级"""
    match = re.match(r"^(#{1,6})\s", line)
    if match:
        return len(match.group(1))
    return 0


def _strip_markdown(text: str) -> str:
    """去除 Markdown 标记，保留纯文本"""
    # 去除标题 #
    text = re.sub(r"^#{1,6}\s+", "", text)
    # 去除加粗/斜体
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    # 去除行内代码
    text = re.sub(r"`(.+?)`", r"\1", text)
    # 去除链接 [text](url)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    # 去除高亮 ==text==
    text = re.sub(r"==(.+?)==", r"\1", text)
    # 去除删除线 ~~text~~
    text = re.sub(r"~~(.+?)~~", r"\1", text)
    return text.strip()


def _has_emphasis(text: str) -> bool:
    """检测是否包含加粗或高亮"""
    return bool(re.search(r"\*\*.+?\*\*", text)) or bool(re.search(r"==.+?==", text))
