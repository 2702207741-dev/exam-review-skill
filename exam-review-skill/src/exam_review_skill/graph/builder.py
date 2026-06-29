"""
知识图谱构建器

从 LLM 分析结果构建 NetworkX 知识图谱。
"""

from __future__ import annotations

import hashlib

from .models import KnowledgeGraph, GraphNode, GraphEdge


def build_graph(analysis_result: dict, course_name: str = "") -> KnowledgeGraph:
    """
    从 LLM 分析结果构建知识图谱。

    Args:
        analysis_result: analyze_chunks() 的返回结果
        course_name: 课程名称

    Returns:
        KnowledgeGraph
    """
    kg = KnowledgeGraph(course_name=course_name)

    kps = analysis_result.get("knowledge_points", [])
    relations = analysis_result.get("relationships", [])

    # 1. 添加节点
    for kp in kps:
        node_id = _make_node_id(kp.get("name", ""))
        node = GraphNode(
            id=node_id,
            name=kp.get("name", ""),
            node_type=kp.get("type", "concept"),
            importance=kp.get("importance", "normal"),
            content=kp.get("content", kp.get("source_hint", "")),
            sources=kp.get("sources", []),
        )
        kg.add_node(node)

    # 2. 添加边
    for rel in relations:
        src_name = rel.get("source", "")
        tgt_name = rel.get("target", "")
        src_id = _make_node_id(src_name)
        tgt_id = _make_node_id(tgt_name)

        if src_id in kg.nodes and tgt_id in kg.nodes:
            edge_type = rel.get("type", "CONTAINS")
            # 标准化 edge type
            edge_type = _normalize_edge_type(edge_type)
            edge = GraphEdge(
                source=src_id,
                target=tgt_id,
                edge_type=edge_type,
                weight=rel.get("weight", 0.5),
                reason=rel.get("reason", ""),
            )
            kg.add_edge(edge)

    # 3. 补充层级包含关系（如果 LLM 没给）
    _add_hierarchy_edges(kg, kps)

    return kg


def build_graph_rule_fallback(tree, course_name: str = "") -> KnowledgeGraph:
    """
    从 v1 规则引擎知识树构建图谱（离线降级用）。

    Args:
        tree: KnowledgeNode 根节点
        course_name: 课程名称

    Returns:
        KnowledgeGraph
    """
    kg = KnowledgeGraph(course_name=course_name)

    # 添加节点
    for node in tree.iter_nodes():
        # 根节点也加入图谱（作为课程名节点）
        node_id = _make_node_id(node.name)
        gn = GraphNode(
            id=node_id,
            name=node.name,
            node_type="concept",
            importance=node.importance if node.level > 0 else "normal",
            content="\n".join(node.content_items[:10]),
            sources=node.sources,
        )
        kg.add_node(gn)

    # 添加层级边
    for node in tree.iter_nodes():
        if node.level == 0:
            continue
        parent = node.parent
        if parent and parent.level >= 0:
            edge = GraphEdge(
                source=_make_node_id(parent.name),
                target=_make_node_id(node.name),
                edge_type="CONTAINS",
                weight=0.5,
            )
            kg.add_edge(edge)

    return kg


def _make_node_id(name: str) -> str:
    """从名称生成节点 ID"""
    return hashlib.md5(name.encode()).hexdigest()[:12]


def _normalize_edge_type(raw: str) -> str:
    """标准化边类型"""
    raw_upper = raw.upper().replace("-", "_").replace(" ", "_")
    valid = {"PREREQUISITE", "CONTAINS", "SIMILAR_TO", "CONFUSED_WITH", "DERIVES_FROM"}
    if raw_upper in valid:
        return raw_upper
    # 模糊匹配
    mapping = {
        "PREREQ": "PREREQUISITE",
        "DEPENDS": "PREREQUISITE",
        "REQUIRES": "PREREQUISITE",
        "HAS": "CONTAINS",
        "INCLUDES": "CONTAINS",
        "SIMILAR": "SIMILAR_TO",
        "LIKE": "SIMILAR_TO",
        "CONFUSE": "CONFUSED_WITH",
        "DERIVES": "DERIVES_FROM",
    }
    for key, val in mapping.items():
        if key in raw_upper:
            return val
    return "CONTAINS"


def _add_hierarchy_edges(kg: KnowledgeGraph, kps: list[dict]) -> None:
    """补充层级包含关系"""
    # 简单策略：level 差 1 且名称相关的节点加 CONTAINS
    sorted_kps = sorted(kps, key=lambda k: k.get("level", 1))
    for i, parent in enumerate(sorted_kps):
        parent_level = parent.get("level", 1)
        parent_id = _make_node_id(parent.get("name", ""))
        if parent_id not in kg.nodes:
            continue
        for child in sorted_kps[i + 1:]:
            child_level = child.get("level", 1)
            if child_level == parent_level + 1:
                child_id = _make_node_id(child.get("name", ""))
                if child_id in kg.nodes:
                    # 检查是否已有边
                    existing = any(
                        e.source == parent_id and e.target == child_id
                        for e in kg.edges
                    )
                    if not existing:
                        kg.add_edge(GraphEdge(
                            source=parent_id,
                            target=child_id,
                            edge_type="CONTAINS",
                            weight=0.3,
                            reason="层级包含",
                        ))
