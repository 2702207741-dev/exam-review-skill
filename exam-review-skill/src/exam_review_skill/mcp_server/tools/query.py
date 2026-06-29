"""
MCP Tool: query_knowledge_graph

查询知识图谱中的关系。
"""

from __future__ import annotations

import json


def query_graph_tool(query_type: str, node_id: str = "",
                      keyword: str = "", depth: int = 1) -> str:
    """
    MCP Tool: query_knowledge_graph

    Args:
        query_type: prerequisites / learning_path / similar / confusion / search / stats / subgraph
        node_id: 目标节点 ID（部分查询需要）
        keyword: 搜索关键词
        depth: 子图深度（subgraph 用）

    Returns:
        JSON 字符串
    """
    try:
        from ...graph import (
            find_prerequisites, find_learning_path,
            find_similar_concepts, find_confusion_pairs,
            get_subgraph, search_nodes, get_statistics,
        )
        from ...graph.models import KnowledgeGraph
        import os, json as _json

        # 从缓存/会话中获取当前图谱（简化：从环境变量或临时文件）
        # 在实际 MCP 会话中，图谱由 server 管理
        # 这里做简化：重新加载最近的图谱文件
        kg_file = os.environ.get("EXAM_REVIEW_KG_FILE", "")
        if kg_file and os.path.exists(kg_file):
            with open(kg_file) as f:
                raw = _json.load(f)
            kg = _load_kg_from_dict(raw)
        else:
            return json.dumps({
                "error": "知识图谱未加载。请先调用 parse_material 或 generate_review。",
                "code": 400,
            }, ensure_ascii=False)

        result = {}

        if query_type == "prerequisites":
            result["prerequisites"] = find_prerequisites(kg, node_id) if node_id else []
        elif query_type == "learning_path":
            result["paths"] = find_learning_path(kg, node_id) if node_id else []
        elif query_type == "similar":
            result["similar"] = find_similar_concepts(kg, node_id) if node_id else []
        elif query_type == "confusion":
            result["confusion_pairs"] = find_confusion_pairs(kg)
        elif query_type == "search":
            result["results"] = search_nodes(kg, keyword) if keyword else []
        elif query_type == "stats":
            result["stats"] = get_statistics(kg)
        elif query_type == "subgraph":
            if node_id:
                ids = [node_id]
                result["subgraph"] = get_subgraph(kg, ids, depth)
            else:
                result["error"] = "subgraph 查询需要 node_id"
        else:
            result["error"] = f"不支持的查询类型: {query_type}"
            result["supported"] = [
                "prerequisites", "learning_path", "similar",
                "confusion", "search", "stats", "subgraph"
            ]

        result["code"] = 0
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "code": 500,
        }, ensure_ascii=False)


def _load_kg_from_dict(data: dict) -> KnowledgeGraph:
    """从字典加载 KnowledgeGraph"""
    from ...graph.models import KnowledgeGraph, GraphNode, GraphEdge
    kg = KnowledgeGraph(course_name=data.get("course_name", ""))
    for n in data.get("nodes", []):
        kg.add_node(GraphNode(
            id=n["id"], name=n["name"], node_type=n.get("type", "concept"),
            importance=n.get("importance", "normal"),
            content=n.get("content", ""), sources=n.get("sources", []),
        ))
    for e in data.get("edges", []):
        kg.add_edge(GraphEdge(
            source=e["source"], target=e["target"],
            edge_type=e.get("type", "CONTAINS"),
            weight=e.get("weight", 0.5), reason=e.get("reason", ""),
        ))
    return kg
