"""
LLM 模块单元测试
"""

import pytest


class TestLLMClient:
    def test_client_without_key_is_unavailable(self):
        from exam_review_skill.llm.client import LLMClient
        client = LLMClient(api_key="")
        assert not client.available

    def test_client_with_key_is_available(self):
        from exam_review_skill.llm.client import LLMClient
        client = LLMClient(api_key="sk-test123")
        assert client.available

    def test_get_client_singleton(self):
        from exam_review_skill.llm.client import get_client, _global_client
        # 重置单例
        import exam_review_skill.llm.client as client_mod
        client_mod._global_client = None
        c1 = get_client()
        c2 = get_client()
        assert c1 is c2

    def test_cache_set_get(self):
        from exam_review_skill.llm.client import LLMClient
        client = LLMClient(api_key="")
        client._cache_set("key1", "value1")
        assert client._cache_get("key1") == "value1"

    def test_cache_expiry(self):
        import time
        from exam_review_skill.llm.client import LLMClient
        client = LLMClient(api_key="", cache_ttl=0)
        client._cache_set("key2", "value2")
        time.sleep(0.01)
        assert client._cache_get("key2") is None


class TestChunker:
    def test_chunk_single_paragraph(self):
        from exam_review_skill.llm.chunker import chunk_paragraphs
        from exam_review_skill.parser.models import Paragraph

        paras = [Paragraph(text="Hello World", level=1)]
        result = chunk_paragraphs(paras, "test.txt")
        assert result.total_chunks == 1
        assert "Hello World" in result.chunks[0].text

    def test_chunk_splits_on_heading(self):
        from exam_review_skill.llm.chunker import chunk_paragraphs
        from exam_review_skill.parser.models import Paragraph

        paras = [
            Paragraph(text="Chapter 1", level=1),
            Paragraph(text="A" * 2500, level=0),
            Paragraph(text="Chapter 2", level=1),
            Paragraph(text="B" * 1000, level=0),
        ]
        result = chunk_paragraphs(paras, "test.txt", max_chars=3000)
        assert result.total_chunks >= 1

    def test_chunk_empty(self):
        from exam_review_skill.llm.chunker import chunk_paragraphs
        result = chunk_paragraphs([], "test.txt")
        assert result.total_chunks == 0


class TestPrompts:
    def test_render_prompt(self):
        from exam_review_skill.llm.prompts import render_prompt
        result = render_prompt("Hello {name}", name="World")
        assert result == "Hello World"

    def test_extract_prompt_has_source_hint(self):
        from exam_review_skill.llm.prompts import EXTRACT_KNOWLEDGE_POINTS
        assert "source_hint" in EXTRACT_KNOWLEDGE_POINTS


class TestQuestionGen:
    def test_rule_based_fallback(self):
        from exam_review_skill.llm.question_gen import _generate_rule_based
        kp = {"name": "测试概念", "content": "这是测试内容"}
        questions = _generate_rule_based(kp, count=2, question_type="choice")
        assert len(questions) == 2
        for q in questions:
            assert "type" in q
            assert "question" in q
            assert "answer" in q

    def test_fill_question(self):
        from exam_review_skill.llm.question_gen import _generate_rule_based
        kp = {"name": "定义", "content": "核心内容"}
        qs = _generate_rule_based(kp, count=1, question_type="fill")
        assert qs[0]["type"] == "fill"


class TestFallback:
    def test_run_rule_fallback(self):
        from exam_review_skill.llm.fallback import run_rule_fallback
        from exam_review_skill.parser.models import ParsedDocument

        doc = ParsedDocument(file_path="test.md", file_type="md")
        doc.add_paragraph("## 测试标题：Python 基础知识概述", level=2)
        doc.add_paragraph("正文内容：Python 是一种解释型、面向对象的高级编程语言，由 Guido van Rossum 于 1991 年首次发布。其设计哲学强调代码可读性和简洁语法。", level=0)
        doc.add_paragraph("### 子标题：变量与数据类型详解", level=3)
        doc.add_paragraph("变量是存储数据的容器，Python 支持动态类型，无需声明变量类型即可直接赋值使用。", level=0)

        result = run_rule_fallback([doc])
        assert result["analysis_mode"] == "rule_fallback"
        assert len(result["knowledge_points"]) >= 2
        assert len(result["relationships"]) >= 1
