"""
离线降级包装器

当 LLM API 不可用时，自动降级到 v1.0 规则引擎。
"""

from __future__ import annotations

from typing import Any


def run_rule_fallback(parsed_docs: list) -> dict[str, Any]:
    """
    Tier 1 降级：使用 v1.0 规则引擎做分析。

    Args:
        parsed_docs: ParsedDocument 列表

    Returns:
        与 LLM 分析同格式的结果，标注 analysis_mode: "rule_fallback"
    """
    from ..structurer import build_knowledge_tree
    from ..parser.models import ParsedDocument

    tree = build_knowledge_tree(parsed_docs)

    # 从知识树提取知识点
    kps = []
    for node in tree.iter_nodes():
        if node.level > 0:
            kps.append({
                "name": node.name,
                "level": node.level,
                "importance": node.importance,
                "type": _infer_type(node.name, node.content_items),
                "prerequisites": [],
                "source_hint": "",
                "sources": node.sources,
                "content": "\n".join(node.content_items[:10]),
            })

    # 规则引擎的关系发现很弱，只做 CONTAINS
    relationships = []
    for node in tree.iter_nodes():
        for child in node.children:
            if child.level > 0:
                relationships.append({
                    "source": node.name if node.level > 0 else "ROOT",
                    "target": child.name,
                    "type": "CONTAINS",
                    "weight": 0.5,
                    "reason": "层级包含",
                })

    return {
        "knowledge_points": kps,
        "relationships": relationships,
        "analysis_mode": "rule_fallback",
        "chunks_processed": 0,
    }


def _infer_type(name: str, content_items: list[str]) -> str:
    """从名称和内容推断知识点类型"""
    combined = name + " " + " ".join(content_items)
    if any(kw in combined for kw in ["定义", "概念", "是指"]):
        return "definition"
    if any(kw in combined for kw in ["定理", "定律", "原理"]):
        return "theorem"
    if any(kw in combined for kw in ["公式", "=", "计算"]):
        return "formula"
    if any(kw in combined for kw in ["例", "例题"]):
        return "example"
    return "concept"
