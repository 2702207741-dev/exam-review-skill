"""
知识图谱模块单元测试
"""

import pytest


class TestGraphModels:
    def test_create_node(self):
        from exam_review_skill.graph.models import GraphNode
        node = GraphNode(
            id="test1",
            name="测试节点",
            node_type="definition",
            importance="high",
        )
        assert node.id == "test1"
        assert node.importance_value == 3
        assert node.radius == 34  # 10 + 3*8
        assert node.color  # 应有颜色

    def test_create_edge(self):
        from exam_review_skill.graph.models import GraphEdge
        edge = GraphEdge(
            source="a",
            target="b",
            edge_type="PREREQUISITE",
            weight=0.9,
        )
        assert edge.color
        assert edge.dash

    def test_knowledge_graph_add(self):
        from exam_review_skill.graph.models import KnowledgeGraph, GraphNode, GraphEdge
        kg = KnowledgeGraph(course_name="测试")
        kg.add_node(GraphNode(id="1", name="A"))
        kg.add_node(GraphNode(id="2", name="B"))
        kg.add_edge(GraphEdge(source="1", target="2", edge_type="PREREQUISITE"))

        assert kg.node_count == 2
        assert kg.edge_count == 1

    def test_knowledge_graph_reject_invalid_edge(self):
        from exam_review_skill.graph.models import KnowledgeGraph, GraphNode, GraphEdge
        kg = KnowledgeGraph()
        kg.add_node(GraphNode(id="1", name="A"))
        kg.add_edge(GraphEdge(source="1", target="2", edge_type="CONTAINS"))
        assert kg.edge_count == 0  # target 不存在

    def test_node_to_dict(self):
        from exam_review_skill.graph.models import GraphNode
        node = GraphNode(id="x", name="X", node_type="theorem")
        d = node.to_dict()
        assert d["id"] == "x"
        assert d["type"] == "theorem"
        assert "color" in d


class TestGraphBuilder:
    def test_build_empty(self):
        from exam_review_skill.graph.builder import build_graph
        result = {"knowledge_points": [], "relationships": []}
        kg = build_graph(result)
        assert kg.node_count == 0

    def test_build_with_kps(self):
        from exam_review_skill.graph.builder import build_graph
        result = {
            "knowledge_points": [
                {"name": "A", "level": 1, "type": "definition", "importance": "high"},
                {"name": "B", "level": 2, "type": "concept", "importance": "normal"},
            ],
            "relationships": [
                {"source": "A", "target": "B", "type": "CONTAINS", "weight": 0.8, "reason": "包含"},
            ],
        }
        kg = build_graph(result)
        assert kg.node_count == 2
        assert kg.edge_count >= 1

    def test_build_rule_fallback(self):
        from exam_review_skill.graph.builder import build_graph_rule_fallback
        from exam_review_skill.structurer.tree_builder import KnowledgeNode

        root = KnowledgeNode(name="课程名", level=0)
        ch1 = KnowledgeNode(name="第一章", level=1, importance="normal")
        ch1.content_items = ["章节内容"]
        root.add_child(ch1)
        ch2 = KnowledgeNode(name="第一节", level=2, importance="normal")
        ch2.content_items = ["节内容"]
        ch1.add_child(ch2)

        kg = build_graph_rule_fallback(root, course_name="测试")
        assert kg.node_count == 3  # 课程名 + 第一章 + 第一节
        assert kg.edge_count == 2  # 课程名→第一章, 第一章→第一节


class TestGraphQuery:
    @pytest.fixture
    def sample_kg(self):
        from exam_review_skill.graph.models import KnowledgeGraph, GraphNode, GraphEdge
        kg = KnowledgeGraph(course_name="测试")
        kg.add_node(GraphNode(id="1", name="基础", node_type="concept"))
        kg.add_node(GraphNode(id="2", name="进阶", node_type="concept"))
        kg.add_node(GraphNode(id="3", name="相似A", node_type="concept"))
        kg.add_node(GraphNode(id="4", name="相似B", node_type="concept"))
        kg.add_edge(GraphEdge(source="1", target="2", edge_type="PREREQUISITE", weight=0.9))
        kg.add_edge(GraphEdge(source="3", target="4", edge_type="SIMILAR_TO", weight=0.7))
        kg.add_edge(GraphEdge(source="3", target="4", edge_type="CONFUSED_WITH", weight=0.5))
        return kg

    def test_find_prerequisites(self, sample_kg):
        from exam_review_skill.graph.query import find_prerequisites
        result = find_prerequisites(sample_kg, "2")
        assert len(result) == 1
        assert result[0]["node"]["name"] == "基础"

    def test_find_similar(self, sample_kg):
        from exam_review_skill.graph.query import find_similar_concepts
        result = find_similar_concepts(sample_kg, "3")
        assert len(result) == 1

    def test_find_confusion_pairs(self, sample_kg):
        from exam_review_skill.graph.query import find_confusion_pairs
        pairs = find_confusion_pairs(sample_kg)
        assert len(pairs) == 1

    def test_search_nodes(self, sample_kg):
        from exam_review_skill.graph.query import search_nodes
        results = search_nodes(sample_kg, "基础")
        assert len(results) == 1
        results2 = search_nodes(sample_kg, "不存在")
        assert len(results2) == 0

    def test_get_statistics(self, sample_kg):
        from exam_review_skill.graph.query import get_statistics
        stats = get_statistics(sample_kg)
        assert stats["total_nodes"] == 4
        assert stats["total_edges"] == 3


class TestGraphExport:
    def test_export_json(self):
        from exam_review_skill.graph.models import KnowledgeGraph, GraphNode
        from exam_review_skill.graph.export import export_json
        kg = KnowledgeGraph(course_name="测试")
        kg.add_node(GraphNode(id="1", name="A"))
        data = export_json(kg)
        assert data["course_name"] == "测试"
        assert len(data["nodes"]) == 1

    def test_export_d3_html_string(self):
        from exam_review_skill.graph.models import KnowledgeGraph, GraphNode
        from exam_review_skill.graph.export import export_d3_html
        kg = KnowledgeGraph(course_name="测试")
        kg.add_node(GraphNode(id="1", name="A", node_type="concept"))
        html = export_d3_html(kg)
        assert "<!DOCTYPE html>" in html
        assert "D3.js" in html or "d3" in html.lower()
        assert "测试" in html
