"""
知识图谱数据模型

定义图节点和边的结构。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


NodeType = Literal[
    "concept", "definition", "theorem", "formula", "example", "question"
]

EdgeType = Literal[
    "PREREQUISITE", "CONTAINS", "SIMILAR_TO",
    "CONFUSED_WITH", "DERIVES_FROM"
]

IMPORTANCE_MAP = {"high": 3, "normal": 2, "low": 1}

NODE_COLORS = {
    "concept":    "#4FC3F7",  # 浅蓝
    "definition": "#81C784",  # 绿
    "theorem":    "#FFB74D",  # 橙
    "formula":    "#E57373",  # 红
    "example":    "#BA68C8",  # 紫
    "question":   "#FFD54F",  # 黄
}

EDGE_COLORS = {
    "PREREQUISITE":   "#F44336",  # 红
    "CONTAINS":       "#2196F3",  # 蓝
    "SIMILAR_TO":     "#4CAF50",  # 绿
    "CONFUSED_WITH":  "#FF9800",  # 橙
    "DERIVES_FROM":   "#9C27B0",  # 紫
}

EDGE_DASHES = {
    "PREREQUISITE":   "5,5",
    "CONTAINS":       "",
    "SIMILAR_TO":     "2,2",
    "CONFUSED_WITH":  "10,5",
    "DERIVES_FROM":   "",
}


@dataclass
class GraphNode:
    """知识图谱节点"""
    id: str
    name: str
    node_type: NodeType = "concept"
    importance: str = "normal"
    content: str = ""
    sources: list[dict] = field(default_factory=list)

    @property
    def importance_value(self) -> int:
        return IMPORTANCE_MAP.get(self.importance, 2)

    @property
    def color(self) -> str:
        return NODE_COLORS.get(self.node_type, "#BDBDBD")

    @property
    def radius(self) -> int:
        return 10 + self.importance_value * 8

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.node_type,
            "importance": self.importance,
            "content": self.content,
            "sources": self.sources,
            "color": self.color,
            "radius": self.radius,
        }


@dataclass
class GraphEdge:
    """知识图谱边"""
    source: str
    target: str
    edge_type: EdgeType = "CONTAINS"
    weight: float = 0.5
    reason: str = ""

    @property
    def color(self) -> str:
        return EDGE_COLORS.get(self.edge_type, "#757575")

    @property
    def dash(self) -> str:
        return EDGE_DASHES.get(self.edge_type, "")

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.edge_type,
            "weight": self.weight,
            "reason": self.reason,
            "color": self.color,
            "dash": self.dash,
        }


@dataclass
class KnowledgeGraph:
    """知识图谱"""
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)
    course_name: str = ""

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        if edge.source in self.nodes and edge.target in self.nodes:
            self.edges.append(edge)

    def get_node(self, node_id: str) -> GraphNode | None:
        return self.nodes.get(node_id)

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    def to_networkx(self):
        """转换为 NetworkX 图"""
        import networkx as nx
        G = nx.DiGraph()

        for node_id, node in self.nodes.items():
            G.add_node(node_id, **node.to_dict())

        for edge in self.edges:
            G.add_edge(edge.source, edge.target, **edge.to_dict())

        return G
