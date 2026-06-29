"""
知识结构化模块入口
"""

from .tree_builder import (
    KnowledgeNode,
    build_knowledge_tree,
    get_top_percent_nodes,
)

__all__ = [
    "KnowledgeNode",
    "build_knowledge_tree",
    "get_top_percent_nodes",
]
