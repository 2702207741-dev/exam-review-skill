"""
Exam Review Skill — 输入输出数据结构定义

遵循标准化接口协议，使用 Pydantic v2 进行严格的参数校验。
"""

from __future__ import annotations

from enum import IntEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


# ============================================================
# 错误码
# ============================================================

class ErrorCode(IntEnum):
    """标准化错误码定义"""
    SUCCESS = 0
    UNSUPPORTED_FORMAT = 1001
    FILE_CORRUPTED = 1002
    EMPTY_CONTENT = 1003
    INVALID_PARAMS = 2001
    PARTIAL_PARSE_FAILURE = 3001


SUPPORTED_FORMATS = frozenset({"pptx", "docx", "pdf", "txt", "md"})
VALID_PRIORITIES = frozenset({"high", "normal", "low"})
VALID_EDUCATION_LEVELS = frozenset({"高中", "本科", "专科", "研究生"})
VALID_EXAM_TYPES = frozenset({"期末", "期中", "补考", "单元测"})
VALID_OUTPUT_MODULES = frozenset({"mind_map", "basic_concepts", "high_freq_points", "error_prone"})
VALID_FOCUS = frozenset({"概念", "公式", "例题", "定理证明", "均衡"})


# ============================================================
# 输入模型
# ============================================================

class CourseInfo(BaseModel):
    """课程信息"""
    course_name: str = Field(..., min_length=1, description="课程名称，必填")
    chapter_scope: str = Field(
        default="全量",
        description="复习章节范围，选填，默认全量"
    )
    education_level: Literal["高中", "本科", "专科", "研究生"] = Field(
        default="本科",
        description="学段"
    )
    exam_type: Literal["期末", "期中", "补考", "单元测"] = Field(
        default="期末",
        description="考试类型"
    )

    @field_validator("course_name")
    @classmethod
    def course_name_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("course_name 不能为空")
        return stripped


class Material(BaseModel):
    """单个素材"""
    file_path: str = Field(..., min_length=1, description="文件本地路径或可读 URL，必填")
    file_type: str = Field(..., description="文件格式：pptx/docx/pdf/txt/md，必填")
    priority: Literal["high", "normal", "low"] = Field(
        default="normal",
        description="素材优先级"
    )

    @field_validator("file_type")
    @classmethod
    def validate_file_type(cls, v: str) -> str:
        v = v.lower().strip().lstrip(".")
        if v not in SUPPORTED_FORMATS:
            raise ValueError(f"不支持的文件格式: {v}，支持的格式: {sorted(SUPPORTED_FORMATS)}")
        return v

    @field_validator("file_path")
    @classmethod
    def file_path_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("file_path 不能为空")
        return v.strip()


class Config(BaseModel):
    """运行配置"""
    mind_map_depth: int = Field(
        default=3,
        ge=1,
        le=8,
        description="思维导图展开层级，1-8"
    )
    output_modules: list[str] = Field(
        default_factory=lambda: ["mind_map", "basic_concepts", "high_freq_points", "error_prone"],
        min_length=1,
        description="要输出的模块列表"
    )
    focus_preference: Literal["概念", "公式", "例题", "定理证明", "均衡"] = Field(
        default="均衡",
        description="侧重方向"
    )

    @field_validator("output_modules")
    @classmethod
    def validate_modules(cls, v: list[str]) -> list[str]:
        for mod in v:
            if mod not in VALID_OUTPUT_MODULES:
                raise ValueError(f"不支持的 output_module: {mod}，支持: {sorted(VALID_OUTPUT_MODULES)}")
        return v


class ExamReviewInput(BaseModel):
    """Skill 统一输入"""
    course_info: CourseInfo
    materials: list[Material] = Field(..., min_length=1)
    config: Config = Field(default_factory=Config)


# ============================================================
# 输出模型
# ============================================================

class SourceInfo(BaseModel):
    """单条溯源信息"""
    file_name: str
    page: int | None = None          # PDF/PPT 页码
    slide: int | None = None         # PPT 幻灯片号
    paragraph: int | None = None     # 段落序号
    priority: str = "normal"


class KnowledgePoint(BaseModel):
    """知识点"""
    id: str
    name: str
    content: str
    level: int = Field(ge=1, le=8, description="层级深度")
    importance: str = "normal"       # high / normal / low
    sources: list[SourceInfo] = Field(default_factory=list)


class HighFreqPoint(BaseModel):
    """高频考点"""
    name: str
    frequency: str                   # 考频描述
    core_content: str
    question_types: list[str] = Field(default_factory=list)
    sources: list[SourceInfo] = Field(default_factory=list)


class ErrorProneItem(BaseModel):
    """易错/易混淆条目"""
    name: str
    type: str                        # "易错" / "易混淆"
    description: str
    comparison: str | None = None    # 易混淆时的对比说明
    sources: list[SourceInfo] = Field(default_factory=list)


class MindMapNode(BaseModel):
    """思维导图节点（JSON 结构）"""
    name: str
    level: int = 1
    importance: str = "normal"
    children: list[MindMapNode] = Field(default_factory=list)
    sources: list[SourceInfo] = Field(default_factory=list)


class CourseSummary(BaseModel):
    """课程摘要"""
    course_name: str
    knowledge_point_count: int
    high_freq_count: int


class ReviewMaterials(BaseModel):
    """三层复习资料"""
    basic_concepts: list[KnowledgePoint] = Field(default_factory=list)
    high_freq_points: list[HighFreqPoint] = Field(default_factory=list)
    error_prone_summary: list[ErrorProneItem] = Field(default_factory=list)


class MindMapOutput(BaseModel):
    """思维导图输出"""
    mermaid_string: str
    json_structure: MindMapNode | None = None


class ExamReviewOutput(BaseModel):
    """Skill 统一输出"""
    code: int = ErrorCode.SUCCESS
    message: str = "执行成功"
    data: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def error(cls, code: ErrorCode, message: str, data: dict[str, Any] | None = None) -> "ExamReviewOutput":
        """便捷构造错误响应"""
        return cls(code=code, message=message, data=data or {})


# ============================================================
# 工具函数
# ============================================================

def validate_input(data: dict[str, Any]) -> ExamReviewInput:
    """校验并解析输入 JSON"""
    return ExamReviewInput.model_validate(data)


def make_output(
    course_summary: CourseSummary,
    mind_map: MindMapOutput | None = None,
    review_materials: ReviewMaterials | None = None,
    source_trace: dict[str, list[SourceInfo]] | None = None,
) -> ExamReviewOutput:
    """构建标准化输出"""
    data: dict[str, Any] = {"course_summary": course_summary.model_dump()}

    if mind_map:
        data["mind_map"] = mind_map.model_dump()
    if review_materials:
        data["review_materials"] = review_materials.model_dump()
    if source_trace:
        data["source_trace"] = source_trace

    return ExamReviewOutput(code=0, message="执行成功", data=data)
