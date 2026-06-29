"""
LLM 语义分析器

主入口：接收分块后的文档，调用 DeepSeek API 做语义分析。
"""

from __future__ import annotations

from typing import Any

from .client import get_client
from .prompts import (
    EXTRACT_KNOWLEDGE_POINTS,
    DISCOVER_RELATIONSHIPS,
    render_prompt,
)
from .chunker import ChunkedDocument, Chunk


def analyze_chunks(
    chunked_doc: ChunkedDocument,
    progress_callback=None,
) -> dict[str, Any]:
    """
    对分块文档做全量语义分析。

    Args:
        chunked_doc: 分块后的文档
        progress_callback: 可选，每完成一个 chunk 调用 callback(chunk_idx, total)

    Returns:
        {
            "knowledge_points": [...],   # 聚合后的知识点列表
            "relationships": [...],       # 关系边列表
            "analysis_mode": "llm",
            "chunks_processed": N,
        }
    """
    client = get_client()

    if not client.available:
        return {
            "knowledge_points": [],
            "relationships": [],
            "analysis_mode": "unavailable",
            "chunks_processed": 0,
        }

    all_kps = []
    chunk_map = chunked_doc.chunk_map

    for i, chunk in enumerate(chunked_doc.chunks):
        # Step 1: 提取知识点
        kps = _extract_from_chunk(client, chunk)
        if kps:
            # 补全 source 信息
            for kp in kps:
                kp["_chunk_index"] = i
                kp["_source_file"] = chunk.source_file
                kp["_source_page"] = chunk.start_page
                kp["_source_para_start"] = chunk.start_para
            all_kps.extend(kps)

        if progress_callback:
            progress_callback(i + 1, chunked_doc.total_chunks)

    # Step 2: 去重 + 合并同名知识点
    merged_kps = _merge_duplicate_kps(all_kps)

    # Step 3: 全局关系发现
    relationships = _discover_relationships(client, merged_kps)

    # Step 4: 后处理 — 从 source_hint 模糊匹配精确来源
    _post_process_sources(merged_kps, chunked_doc)

    return {
        "knowledge_points": merged_kps,
        "relationships": relationships,
        "analysis_mode": "llm",
        "chunks_processed": chunked_doc.total_chunks,
    }


def _extract_from_chunk(client, chunk: Chunk) -> list[dict]:
    """从单个 chunk 提取知识点"""
    prompt = render_prompt(EXTRACT_KNOWLEDGE_POINTS, content=chunk.text)
    messages = [
        {"role": "system", "content": "你是一个课程知识结构分析专家，只输出 JSON。"},
        {"role": "user", "content": prompt},
    ]

    try:
        result = client.chat_json(messages, temperature=0.3)
        if isinstance(result, dict):
            return result.get("knowledge_points", [])
        if isinstance(result, list):
            return result
    except Exception:
        pass

    return []


def _discover_relationships(client, kps: list[dict]) -> list[dict]:
    """全局关系发现"""
    if len(kps) < 2:
        return []

    # 只传名称列表减少 token
    kp_summary = [
        {"name": k["name"], "type": k.get("type", "concept")}
        for k in kps
    ]
    prompt = render_prompt(
        DISCOVER_RELATIONSHIPS,
        knowledge_points=kp_summary,
    )
    messages = [
        {"role": "system", "content": "你是一个知识图谱关系分析专家，只输出 JSON。"},
        {"role": "user", "content": prompt},
    ]

    try:
        result = client.chat_json(messages, temperature=0.3)
        if isinstance(result, dict):
            return result.get("relationships", [])
    except Exception:
        pass

    return []


def _merge_duplicate_kps(kps: list[dict]) -> list[dict]:
    """合并同名知识点（保留 source_hints 最长的那个）"""
    merged: dict[str, dict] = {}
    for kp in kps:
        name = kp.get("name", "")
        if name in merged:
            # 保留更长的 source_hint
            old_hint = merged[name].get("source_hint", "")
            new_hint = kp.get("source_hint", "")
            if len(new_hint) > len(old_hint):
                merged[name] = kp
        else:
            merged[name] = kp
    return list(merged.values())


def _post_process_sources(kps: list[dict],
                           chunked_doc: ChunkedDocument) -> None:
    """
    后处理：用 source_hint 在原文中模糊匹配，补全精确来源。
    将内部字段 _source_* 转为标准 sources 格式。
    """
    for kp in kps:
        sources = []
        source_hint = kp.get("source_hint", "")
        source_file = kp.pop("_source_file", "")
        source_page = kp.pop("_source_page", None)
        source_para = kp.pop("_source_para_start", 0)
        chunk_idx = kp.pop("_chunk_index", 0)

        # 在当前 chunk 中找 source_hint 的精确位置
        chunk = chunked_doc.chunk_map.get(chunk_idx)
        if chunk and source_hint:
            # 在 chunk.text 中搜索 source_hint
            pos = chunk.text.find(source_hint[:30])  # 前 30 字匹配
            if pos >= 0:
                # 计算大致段落偏移
                before_text = chunk.text[:pos]
                para_offset = before_text.count("\n")
                actual_para = chunk.start_para + para_offset
            else:
                actual_para = source_para
        else:
            actual_para = source_para

        sources.append({
            "file_name": source_file,
            "page": source_page,
            "slide": None,
            "paragraph": actual_para,
            "priority": "normal",
        })
        kp["sources"] = sources
