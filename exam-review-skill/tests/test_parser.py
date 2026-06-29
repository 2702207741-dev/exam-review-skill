"""
Parser 模块单元测试
"""

import os
import tempfile
import pytest

from exam_review_skill.parser import parse_material
from exam_review_skill.parser.models import ParsedDocument, Paragraph


class TestTxtParser:
    def test_parse_basic_txt(self):
        content = """第一章 Python基础

1.1 变量
Python是动态类型语言。

1.2 数据类型
包括int, float, str等。
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp_path = f.name

        try:
            doc = parse_material(tmp_path, "txt")
            assert doc.file_type == "txt"
            assert len(doc.paragraphs) > 0
            # 第一章应被识别为标题（level > 0）
            chapter_line = next(
                (p for p in doc.paragraphs if "第一章" in p.text), None
            )
            assert chapter_line is not None
            assert chapter_line.level >= 1
        finally:
            os.unlink(tmp_path)

    def test_empty_txt(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("")
            tmp_path = f.name

        try:
            doc = parse_material(tmp_path, "txt")
            assert doc.is_empty
        finally:
            os.unlink(tmp_path)

    def test_parse_gbk_encoding(self):
        content = "第一章 测试\n这是GBK编码的内容。"
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".txt", delete=False
        ) as f:
            f.write(content.encode("gbk"))
            tmp_path = f.name

        try:
            doc = parse_material(tmp_path, "txt")
            assert len(doc.paragraphs) >= 1
        finally:
            os.unlink(tmp_path)


class TestMarkdownParser:
    def test_parse_headings(self):
        content = """# 一级标题

## 二级标题

正文内容。

### 三级标题

**重点内容**
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp_path = f.name

        try:
            doc = parse_material(tmp_path, "md")
            assert doc.file_type == "md"
            # 应能找到标题段落
            headings = [p for p in doc.paragraphs if p.level > 0]
            assert len(headings) >= 2
            # 一级标题 level=1
            h1 = next((p for p in headings if "一级标题" in p.text), None)
            assert h1 is not None
            assert h1.level == 1
            # 重点标记
            important = [p for p in doc.paragraphs if p.is_important]
            assert len(important) >= 1
        finally:
            os.unlink(tmp_path)

    def test_strip_markdown_tags(self):
        content = "## **加粗标题**"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp_path = f.name

        try:
            doc = parse_material(tmp_path, "md")
            titles = [p for p in doc.paragraphs if p.level > 0]
            assert len(titles) == 1
            assert "**" not in titles[0].text, "Markdown 标记应被去除"
        finally:
            os.unlink(tmp_path)


class TestParserFactory:
    def test_unsupported_format(self):
        with pytest.raises(ValueError, match="不支持的文件格式"):
            parse_material("/tmp/test.exe", "exe")

    def test_file_not_found(self):
        doc = parse_material("/tmp/nonexistent_file_12345.txt", "txt")
        assert len(doc.parse_errors) > 0
        assert doc.is_empty


class TestTextCleaning:
    def test_clean_removes_whitespace(self):
        from exam_review_skill.parser.models import _clean_text
        result = _clean_text("  hello   world  ")
        assert result == "hello world"

    def test_clean_removes_page_numbers(self):
        from exam_review_skill.parser.models import _clean_text
        assert _clean_text("42") == ""
        assert _clean_text("  123  ") == ""


class TestParsedDocument:
    def test_is_empty(self):
        doc = ParsedDocument(file_path="test.txt", file_type="txt")
        assert doc.is_empty

    def test_total_chars(self):
        doc = ParsedDocument(file_path="test.txt", file_type="txt")
        doc.add_paragraph("Hello World")
        assert doc.total_chars == 11
