"""
解析器共享数据模型 — 统一段落结构

所有格式解析器统一输出 ParsedDocument，包含标准化段落列表。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Paragraph:
    """标准化段落"""
    text: str                       # 清洗后的文本内容
    level: int = 1                  # 标题层级（1=最大标题，0=正文）
    is_important: bool = False      # 是否被标记为重点（加粗/高亮/下划线）
    page: int | None = None         # 页码（PDF/PPT）
    slide: int | None = None        # 幻灯片号（PPT）
    para_index: int = 0             # 段落序号
    raw_style: str = ""             # 原始样式名（用于溯源）


@dataclass
class ParsedDocument:
    """解析后的文档"""
    file_path: str
    file_type: str
    paragraphs: list[Paragraph] = field(default_factory=list)
    total_pages: int = 0
    parse_errors: list[str] = field(default_factory=list)
    priority: str = "normal"

    @property
    def total_chars(self) -> int:
        return sum(len(p.text) for p in self.paragraphs)

    @property
    def is_empty(self) -> bool:
        return self.total_chars < 100

    def add_paragraph(self, text: str, level: int = 1,
                      is_important: bool = False, page: int | None = None,
                      slide: int | None = None, raw_style: str = "") -> None:
        """添加一个清洗后的段落"""
        cleaned = _clean_text(text)
        if not cleaned:
            return
        idx = len(self.paragraphs) + 1
        self.paragraphs.append(Paragraph(
            text=cleaned,
            level=level,
            is_important=is_important,
            page=page,
            slide=slide,
            para_index=idx,
            raw_style=raw_style,
        ))


# ---- 文本清洗 ----

def _clean_text(text: str) -> str:
    """清洗文本：去多余空白、归一换行、剔除纯标点行"""
    if not text:
        return ""
    # 归一化空白
    cleaned = " ".join(text.split())
    # 剔除纯标点/数字/符号行（页眉页脚常见）
    stripped = cleaned.strip()
    if not stripped:
        return ""
    # 仅丢弃独立 1-3 位纯数字（大概率页码），保留 4 位以上（年份/编号等）
    if stripped.isdigit() and len(stripped) <= 3:
        return ""
    return stripped
