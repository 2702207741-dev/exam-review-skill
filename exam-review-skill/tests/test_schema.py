"""
Schema 模块单元测试
"""

import pytest
from exam_review_skill.schema.models import (
    CourseInfo, Material, Config, ExamReviewInput,
    ExamReviewOutput, ErrorCode, validate_input, make_output,
    CourseSummary, MindMapOutput, ReviewMaterials,
)


class TestCourseInfo:
    def test_valid_course_info(self):
        ci = CourseInfo(course_name="Python 程序设计")
        assert ci.course_name == "Python 程序设计"
        assert ci.education_level == "本科"
        assert ci.exam_type == "期末"

    def test_empty_course_name_fails(self):
        with pytest.raises(ValueError):
            CourseInfo(course_name="")

    def test_whitespace_only_course_name_fails(self):
        with pytest.raises(ValueError):
            CourseInfo(course_name="   ")

    def test_invalid_education_level_fails(self):
        with pytest.raises(ValueError):
            CourseInfo(course_name="Test", education_level="小学")

    def test_invalid_exam_type_fails(self):
        with pytest.raises(ValueError):
            CourseInfo(course_name="Test", exam_type="月考")


class TestMaterial:
    def test_valid_material(self):
        m = Material(file_path="/tmp/test.pdf", file_type="pdf")
        assert m.file_type == "pdf"
        assert m.priority == "normal"

    def test_unsupported_format_fails(self):
        with pytest.raises(ValueError):
            Material(file_path="/tmp/test.xls", file_type="xls")

    def test_case_insensitive_format(self):
        m = Material(file_path="/tmp/test.PDF", file_type="PDF")
        assert m.file_type == "pdf"

    def test_invalid_priority_fails(self):
        with pytest.raises(ValueError):
            Material(file_path="/tmp/test.pdf", file_type="pdf", priority="urgent")


class TestConfig:
    def test_default_config(self):
        c = Config()
        assert c.mind_map_depth == 3
        assert "mind_map" in c.output_modules
        assert c.focus_preference == "均衡"

    def test_depth_bounds(self):
        with pytest.raises(ValueError):
            Config(mind_map_depth=0)
        with pytest.raises(ValueError):
            Config(mind_map_depth=9)

    def test_invalid_output_module_fails(self):
        with pytest.raises(ValueError):
            Config(output_modules=["invalid_module"])


class TestExamReviewInput:
    def test_minimal_valid_input(self):
        data = {
            "course_info": {"course_name": "Test"},
            "materials": [{"file_path": "/tmp/test.md", "file_type": "md"}],
        }
        result = validate_input(data)
        assert result.course_info.course_name == "Test"
        assert len(result.materials) == 1

    def test_empty_materials_fails(self):
        data = {
            "course_info": {"course_name": "Test"},
            "materials": [],
        }
        with pytest.raises(ValueError):
            validate_input(data)

    def test_missing_course_info_fails(self):
        data = {
            "materials": [{"file_path": "/tmp/test.md", "file_type": "md"}],
        }
        with pytest.raises(ValueError):
            validate_input(data)


class TestErrorCode:
    def test_error_codes(self):
        assert ErrorCode.SUCCESS == 0
        assert ErrorCode.UNSUPPORTED_FORMAT == 1001
        assert ErrorCode.INVALID_PARAMS == 2001


class TestExamReviewOutput:
    def test_success_output(self):
        summary = CourseSummary(
            course_name="Test",
            knowledge_point_count=10,
            high_freq_count=3,
        )
        output = make_output(course_summary=summary)
        assert output.code == 0
        assert output.data["course_summary"]["knowledge_point_count"] == 10

    def test_error_output(self):
        output = ExamReviewOutput.error(
            ErrorCode.INVALID_PARAMS,
            "测试错误",
        )
        assert output.code == 2001
        assert "测试错误" in output.message
