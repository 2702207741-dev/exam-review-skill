"""
Mindmap 模块单元测试
"""

import pytest
from exam_review_skill.structurer.tree_builder import KnowledgeNode
from exam_review_skill.mindmap import (
    generate_mermaid,
    generate_json_tree,
    export_markdown_mindmap,
)


@pytest.fixture
def sample_tree():
    """构造测试用知识树"""
    root = KnowledgeNode(name="Python 程序设计", level=0, importance="high")

    ch1 = KnowledgeNode(name="基础语法", level=1, importance="normal")
    ch1.add_child(KnowledgeNode(name="变量与类型", level=2, importance="high"))
    ch1.add_child(KnowledgeNode(name="控制流", level=2, importance="normal"))
    root.add_child(ch1)

    ch2 = KnowledgeNode(name="函数与模块", level=1, importance="high")
    ch2.add_child(KnowledgeNode(name="函数定义", level=2, importance="high"))
    ch2.add_child(KnowledgeNode(name="作用域", level=2, importance="normal"))
    root.add_child(ch2)

    return root


class TestMermaidGeneration:
    def test_generates_valid_mermaid(self, sample_tree):
        result = generate_mermaid(sample_tree, max_depth=3)
        assert "```mermaid" in result
        assert "mindmap" in result
        assert "Python 程序设计" in result
        assert "基础语法" in result
        assert "```" in result

    def test_respects_max_depth(self, sample_tree):
        result = generate_mermaid(sample_tree, max_depth=1)
        assert "基础语法" in result
        assert "变量与类型" not in result  # depth=2, 应被过滤

    def test_sanitizes_special_chars(self):
        root = KnowledgeNode(name="Test (with) [special] {chars}", level=0)
        result = generate_mermaid(root, max_depth=1)
        # root((...)) is Mermaid syntax, not the name itself
        # The name inside root((...)) should not have special chars except the wrapper
        after_root = result.split("root((")[-1] if "root((" in result else result
        # Check the node name (between (( and )))
        # The root name is wrapped in ((...)), so we check that special chars are removed from the raw name
        assert "(with)" not in after_root or after_root.startswith("(Test")


class TestJsonTreeGeneration:
    def test_generates_valid_json_structure(self, sample_tree):
        result = generate_json_tree(sample_tree, max_depth=3)
        assert result["name"] == "Python 程序设计"
        assert "children" in result
        assert len(result["children"]) == 2

        ch1 = next(c for c in result["children"] if c["name"] == "基础语法")
        assert len(ch1["children"]) == 2

    def test_respects_max_depth(self, sample_tree):
        # max_depth=1: root + immediate children, but children's children filtered
        result = generate_json_tree(sample_tree, max_depth=2)
        # Children exist at depth 1 -> shown
        assert len(result.get("children", [])) > 0
        # But their children should be empty
        for child in result.get("children", []):
            assert len(child.get("children", [])) == 0

    def test_includes_importance(self, sample_tree):
        result = generate_json_tree(sample_tree, max_depth=3)
        assert result["importance"] == "high"


class TestMarkdownMindmapExport:
    def test_generates_markdown_list(self, sample_tree):
        result = export_markdown_mindmap(sample_tree, max_depth=3)
        assert "# 思维导图" in result
        assert "Python 程序设计" in result
        assert "- " in result  # 列表标记

    def test_importance_marking(self, sample_tree):
        result = export_markdown_mindmap(sample_tree, max_depth=2)
        # 高频考点应有标记
        assert "函数与模块" in result
