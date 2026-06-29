"""
语义分块器

将 ParsedDocument 切成 LLM 友好的 chunks，同时记录 chunk→source 映射。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Chunk:
    """一个语义块"""
    text: str
    source_file: str
    start_page: int | None = None
    start_slide: int | None = None
    start_para: int = 0
    end_para: int = 0
    chunk_index: int = 0

    def __hash__(self) -> int:
        return hash((self.source_file, self.chunk_index))


@dataclass
class ChunkedDocument:
    """分块后的文档"""
    chunks: list[Chunk] = field(default_factory=list)
    total_chunks: int = 0

    @property
    def chunk_map(self) -> dict[int, Chunk]:
        """chunk_index → Chunk 映射"""
        return {c.chunk_index: c for c in self.chunks}


def chunk_paragraphs(paragraphs: list, source_file: str,
                     max_chars: int = 3000) -> ChunkedDocument:
    """
    将段落列表切成语义块。

    策略：
    - 以标题段落为自然分割点（遇到 level>0 的段落时尽量不切断）
    - 每个 chunk 不超过 max_chars
    - 记录每个 chunk 的来源段落范围

    Args:
        paragraphs: Paragraph 对象列表
        source_file: 来源文件路径
        max_chars: 每个 chunk 最大字符数

    Returns:
        ChunkedDocument
    """
    doc = ChunkedDocument()
    chunks: list[Chunk] = []
    current_text = ""
    current_start = 0
    current_page = None
    current_slide = None
    chunk_idx = 0

    for i, para in enumerate(paragraphs):
        para_text = para.text if hasattr(para, 'text') else str(para)
        para_level = para.level if hasattr(para, 'level') else 0
        para_page = para.page if hasattr(para, 'page') else None
        para_slide = para.slide if hasattr(para, 'slide') else None

        # 标题段落 → 优先在此处切割
        should_split = (
            para_level > 0
            and len(current_text) + len(para_text) > max_chars * 0.7
        )

        if should_split and current_text:
            chunks.append(Chunk(
                text=current_text.strip(),
                source_file=source_file,
                start_page=current_page,
                start_slide=current_slide,
                start_para=current_start,
                end_para=i - 1,
                chunk_index=chunk_idx,
            ))
            chunk_idx += 1
            current_text = para_text + "\n"
            current_start = i
            current_page = para_page
            current_slide = para_slide
        else:
            if not current_text:
                current_start = i
                current_page = para_page
                current_slide = para_slide
            current_text += para_text + "\n"

        # 超限强制切割
        if len(current_text) > max_chars:
            chunks.append(Chunk(
                text=current_text[:max_chars].strip(),
                source_file=source_file,
                start_page=current_page,
                start_slide=current_slide,
                start_para=current_start,
                end_para=i,
                chunk_index=chunk_idx,
            ))
            chunk_idx += 1
            current_text = current_text[max_chars:]
            current_start = i

    # 最后一个 chunk
    if current_text.strip():
        chunks.append(Chunk(
            text=current_text.strip(),
            source_file=source_file,
            start_page=current_page,
            start_slide=current_slide,
            start_para=current_start,
            end_para=len(paragraphs) - 1,
            chunk_index=chunk_idx,
        ))
        chunk_idx += 1

    doc.chunks = chunks
    doc.total_chunks = len(chunks)
    return doc


def chunk_from_parsed_doc(parsed_doc) -> ChunkedDocument:
    """从 ParsedDocument (v1) 创建分块"""
    paragraphs = parsed_doc.paragraphs
    source_file = parsed_doc.file_path
    return chunk_paragraphs(paragraphs, source_file)
