"""
TXT 文本解析器

按行读取，通过缩进、前缀模式推断标题层级。
"""

from __future__ import annotations

import re

from .models import ParsedDocument


def parse_txt(file_path: str, priority: str = "normal") -> ParsedDocument:
    """解析 TXT 文件，返回 ParsedDocument"""
    doc = ParsedDocument(
        file_path=file_path,
        file_type="txt",
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
            doc.parse_errors.append(f"无法读取 TXT 文件: {e}")
            return doc
    except Exception as e:
        doc.parse_errors.append(f"无法打开 TXT 文件: {e}")
        return doc

    if not content.strip():
        doc.parse_errors.append("文件内容为空")
        return doc

    lines = content.split("\n")
    doc.total_pages = 1

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        level = _infer_txt_level(stripped)
        is_important = _is_important_line(stripped)

        doc.add_paragraph(stripped, level=level, is_important=is_important)

    return doc


def _infer_txt_level(line: str) -> int:
    """通过前缀模式推断 TXT 行层级"""
    # "第X章" → level 1
    if re.match(r"^第[一二三四五六七八九十\d]+[章节]", line):
        return 1

    # 数字编号 → level 取决于深度
    if re.match(r"^\d+[\.\、\)]", line):
        return 2
    if re.match(r"^\d+\.\d+[\.\、\)]?", line):
        return 3
    if re.match(r"^\d+\.\d+\.\d+", line):
        return 4

    # 中文编号 "一、" → level 1
    if re.match(r"^[一二三四五六七八九十]+[、．]", line):
        return 1
    # "（一）" → level 2
    if re.match(r"^（[一二三四五六七八九十]+）", line):
        return 2

    # 全大写/CAPS 短行 → 可能是标题
    if len(line) < 30 and line.isupper():
        return 1

    return 0


def _is_important_line(line: str) -> bool:
    """检测是否为重要行"""
    if "注意" in line or "重点" in line or "考点" in line:
        return True
    if "定义" in line or "定理" in line or "公式" in line:
        return True
    return False
