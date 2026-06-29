"""
多格式素材解析模块

提供统一入口 parse_material()，根据文件类型自动分发到对应解析器。
"""

from __future__ import annotations

from .models import ParsedDocument, Paragraph
from .pptx_parser import parse_pptx
from .docx_parser import parse_docx
from .pdf_parser import parse_pdf
from .txt_parser import parse_txt
from .md_parser import parse_md

PARSER_MAP = {
    "pptx": parse_pptx,
    "docx": parse_docx,
    "pdf":  parse_pdf,
    "txt":  parse_txt,
    "md":   parse_md,
}


def parse_material(file_path: str, file_type: str,
                   priority: str = "normal") -> ParsedDocument:
    """
    统一解析入口。

    Args:
        file_path: 文件路径
        file_type: 文件类型 (pptx/docx/pdf/txt/md)
        priority: 素材优先级 (high/normal/low)

    Returns:
        ParsedDocument 对象，包含标准化段落列表

    Raises:
        ValueError: 不支持的文件格式
    """
    file_type = file_type.lower().strip().lstrip(".")
    parser = PARSER_MAP.get(file_type)
    if parser is None:
        raise ValueError(
            f"不支持的文件格式: {file_type}，"
            f"支持的格式: {sorted(PARSER_MAP.keys())}"
        )
    return parser(file_path, priority=priority)


def parse_materials(materials: list[dict]) -> list[ParsedDocument]:
    """
    批量解析素材，单文件失败不中断。

    Args:
        materials: 素材列表，每项包含 file_path, file_type, priority

    Returns:
        ParsedDocument 列表（含部分失败的文件）
    """
    results: list[ParsedDocument] = []
    for mat in materials:
        parsed = parse_material(
            file_path=mat["file_path"],
            file_type=mat["file_type"],
            priority=mat.get("priority", "normal"),
        )
        results.append(parsed)
    return results


__all__ = [
    "parse_material",
    "parse_materials",
    "ParsedDocument",
    "Paragraph",
    "PARSER_MAP",
]
