"""
LLM 语义引擎模块

提供 DeepSeek API 驱动的语义分析能力，包含离线降级。
"""

from .client import LLMClient, get_client
from .chunker import chunk_paragraphs, chunk_from_parsed_doc, Chunk, ChunkedDocument
from .analyzer import analyze_chunks
from .fallback import run_rule_fallback
from .question_gen import generate_questions

__all__ = [
    "LLMClient",
    "get_client",
    "chunk_paragraphs",
    "chunk_from_parsed_doc",
    "Chunk",
    "ChunkedDocument",
    "analyze_chunks",
    "run_rule_fallback",
    "generate_questions",
]
