"""
知识图谱查询 API

提供前置依赖、学习路径、相似概念、混淆对、子图导出等查询。
"""

from __future__ import annotations

from .models import KnowledgeGraph, GraphNode, GraphEdge


def find_prerequisites(kg: KnowledgeGraph, node_id: str) -> list[dict]:
    """查找节点的前置依赖链（递归向上）"""
    result = []
    visited = set()

    def _dfs(current_id: str, depth: int = 0):
        if current_id in visited:
            return
        visited.add(current_id)

        for edge in kg.edges:
            if edge.target == current_id and edge.edge_type == "PREREQUISITE":
                src_node = kg.get_node(edge.source)
                if src_node:
                    result.append({
                        "node": src_node.to_dict(),
                        "depth": depth,
                        "reason": edge.reason,
                    })
                    _dfs(edge.source, depth + 1)

    _dfs(node_id)
    return sorted(result, key=lambda x: x["depth"])


def find_learning_path(kg: KnowledgeGraph,
                        target_id: str) -> list[list[str]]:
    """找到达目标节点的最短学习路径（拓扑排序）"""
    G = kg.to_networkx()

    # 找所有入度为 0 的节点作为起点
    sources = [n for n in G.nodes() if G.in_degree(n) == 0]
    if not sources:
        return []

    paths = []
    try:
        # 简单 BFS 找最短路径
        from collections import deque
        for src in sources:
            if src == target_id:
                continue
            queue = deque([[src]])
            visited = {src}
            found = False
            while queue and not found:
                path = queue.popleft()
                node = path[-1]
                if node == target_id:
                    node_paths = [
                        (kg.get_node(n).name if kg.get_node(n) else n)
                        for n in path
                    ]
                    paths.append(node_paths)
                    found = True
                    break
                for succ in G.successors(node):
                    if succ not in visited:
                        visited.add(succ)
                        queue.append(path + [succ])
    except Exception:
        pass

    return paths


def find_similar_concepts(kg: KnowledgeGraph,
                           node_id: str) -> list[dict]:
    """查找与指定节点相似的概念"""
    result = []
    for edge in kg.edges:
        if edge.edge_type == "SIMILAR_TO":
            if edge.source == node_id:
                tgt = kg.get_node(edge.target)
                if tgt:
                    result.append({"node": tgt.to_dict(), "reason": edge.reason})
            elif edge.target == node_id:
                src = kg.get_node(edge.source)
                if src:
                    result.append({"node": src.to_dict(), "reason": edge.reason})
    return result


def find_confusion_pairs(kg: KnowledgeGraph) -> list[dict]:
    """查找所有易混淆概念对"""
    pairs = []
    seen = set()
    for edge in kg.edges:
        if edge.edge_type == "CONFUSED_WITH":
            pair_key = tuple(sorted([edge.source, edge.target]))
            if pair_key not in seen:
                seen.add(pair_key)
                src = kg.get_node(edge.source)
                tgt = kg.get_node(edge.target)
                if src and tgt:
                    pairs.append({
                        "node_a": src.to_dict(),
                        "node_b": tgt.to_dict(),
                        "reason": edge.reason,
                    })
    return pairs


def get_subgraph(kg: KnowledgeGraph, node_ids: list[str],
                  depth: int = 1) -> dict:
    """导出子图（指定节点 + N 跳邻居）"""
    G = kg.to_networkx()
    selected = set(node_ids)

    for _ in range(depth):
        neighbors = set()
        for n in selected:
            neighbors.update(G.predecessors(n))
            neighbors.update(G.successors(n))
        selected.update(neighbors)

    sub_nodes = []
    for nid in selected:
        node = kg.get_node(nid)
        if node:
            sub_nodes.append(node.to_dict())

    sub_edges = []
    for edge in kg.edges:
        if edge.source in selected and edge.target in selected:
            sub_edges.append(edge.to_dict())

    return {"nodes": sub_nodes, "edges": sub_edges}


def search_nodes(kg: KnowledgeGraph, keyword: str) -> list[dict]:
    """按关键词搜索节点（模糊匹配）"""
    keyword_lower = keyword.lower()
    results = []
    for node in kg.nodes.values():
        if keyword_lower in node.name.lower():
            results.append(node.to_dict())
    return results


def get_statistics(kg: KnowledgeGraph) -> dict:
    """图谱统计信息"""
    type_counts = {}
    importance_counts = {"high": 0, "normal": 0, "low": 0}
    edge_type_counts = {}

    for node in kg.nodes.values():
        type_counts[node.node_type] = type_counts.get(node.node_type, 0) + 1
        importance_counts[node.importance] = importance_counts.get(node.importance, 0) + 1

    for edge in kg.edges:
        edge_type_counts[edge.edge_type] = edge_type_counts.get(edge.edge_type, 0) + 1

    return {
        "total_nodes": kg.node_count,
        "total_edges": kg.edge_count,
        "node_types": type_counts,
        "importance_distribution": importance_counts,
        "edge_types": edge_type_counts,
    }
