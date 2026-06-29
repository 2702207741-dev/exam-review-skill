"""
Material 模块单元测试
"""

import pytest
from exam_review_skill.structurer.tree_builder import KnowledgeNode
from exam_review_skill.material import (
    generate_basic_concepts,
    generate_high_freq_points,
    generate_error_prone,
)


@pytest.fixture
def sample_tree():
    """构造测试用知识树"""
    root = KnowledgeNode(name="Python 基础", level=0)

    # 高频知识点
    ch1 = KnowledgeNode(name="变量与类型", level=2, importance="high")
    ch1.content_items = ["Python 是动态类型语言", "变量不需要声明类型"]
    root.add_child(ch1)

    # 普通知识点
    ch2 = KnowledgeNode(name="运算符", level=2, importance="normal")
    ch2.content_items = ["算术运算符: + - * /", "比较运算符: == != > <"]
    root.add_child(ch2)

    # 易错点
    ch3 = KnowledgeNode(name="== vs is", level=2, importance="high")
    ch3.content_items = ["注意：== 比较值，is 比较对象身份"]
    root.add_child(ch3)

    ch4 = KnowledgeNode(name="默认参数陷阱", level=2, importance="normal")
    ch4.content_items = ["易错：可变类型作为默认参数会导致意外行为"]
    root.add_child(ch4)

    return root


class TestBasicConcepts:
    def test_generates_concepts(self, sample_tree):
        concepts = generate_basic_concepts(sample_tree)
        assert len(concepts) >= 3

        names = [c["name"] for c in concepts]
        assert "变量与类型" in names
        assert "运算符" in names

    def test_concept_has_required_fields(self, sample_tree):
        concepts = generate_basic_concepts(sample_tree)
        for c in concepts:
            assert "name" in c
            assert "content" in c
            assert "importance" in c
            assert "sources" in c


class TestHighFreqPoints:
    def test_filters_top_importance(self, sample_tree):
        hf = generate_high_freq_points(sample_tree)
        # 高频考点应包含 importance=high 的节点
        names = [h["name"] for h in hf]
        assert "变量与类型" in names

    def test_has_question_types(self, sample_tree):
        hf = generate_high_freq_points(sample_tree)
        for h in hf:
            assert "question_types" in h
            assert len(h["question_types"]) > 0


class TestErrorProne:
    def test_detects_error_keywords(self, sample_tree):
        errors = generate_error_prone(sample_tree)
        # 应检测到包含"注意""易错"的节点
        names = [e["name"] for e in errors]
        assert "== vs is" in names or "默认参数陷阱" in names

    def test_error_item_structure(self, sample_tree):
        errors = generate_error_prone(sample_tree)
        for e in errors:
            assert "name" in e
            assert "type" in e
            assert e["type"] in ("易错", "易混淆")
            assert "description" in e
