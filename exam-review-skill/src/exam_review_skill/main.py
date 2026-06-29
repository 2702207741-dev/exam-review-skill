"""
Exam Review Skill 核心入口

对外暴露 run() 方法，接收标准化输入 JSON，执行全流程处理，
返回标准化输出 JSON。
"""

from __future__ import annotations

import traceback
from typing import Any

from .schema.models import (
    ExamReviewInput,
    ExamReviewOutput,
    CourseSummary,
    MindMapOutput,
    ReviewMaterials,
    SourceInfo,
    KnowledgePoint,
    HighFreqPoint,
    ErrorProneItem,
    ErrorCode,
    validate_input,
    make_output,
)
from .parser import parse_materials, ParsedDocument
from .structurer import build_knowledge_tree
from .mindmap import generate_mermaid, generate_json_tree
from .material import generate_basic_concepts, generate_high_freq_points, generate_error_prone
from .utils import generate_kp_id


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    """
    执行全流程：解析 → 结构化 → 生成各模块输出。

    Args:
        input_data: 符合接口协议的 JSON 字典

    Returns:
        标准化输出 JSON 字典
    """
    # ---- 1. 参数校验 ----
    try:
        validated = validate_input(input_data)
    except Exception as e:
        return ExamReviewOutput.error(
            ErrorCode.INVALID_PARAMS,
            f"参数校验失败: {e}",
        ).model_dump()

    course = validated.course_info
    materials = validated.materials
    config = validated.config

    # ---- 2. 素材解析 ----
    material_dicts = [m.model_dump() for m in materials]
    parsed_docs = parse_materials(material_dicts)

    # 检查解析结果
    failed_files = [d.file_path for d in parsed_docs if d.parse_errors]
    all_empty = all(d.is_empty for d in parsed_docs)

    if all_empty:
        return ExamReviewOutput.error(
            ErrorCode.EMPTY_CONTENT,
            "所有素材内容为空，请检查文件",
            {"failed_files": [d.file_path for d in parsed_docs]},
        ).model_dump()

    if failed_files:
        # 部分失败
        if len(failed_files) == len(parsed_docs):
            return ExamReviewOutput.error(
                ErrorCode.FILE_CORRUPTED,
                f"全部文件解析失败: {failed_files}",
                {"failed_files": failed_files},
            ).model_dump()

    # ---- 3. 知识结构化 ----
    try:
        tree = build_knowledge_tree(parsed_docs)
    except Exception as e:
        return ExamReviewOutput.error(
            ErrorCode.PARTIAL_PARSE_FAILURE,
            f"知识结构化失败: {e}",
        ).model_dump()

    total_kp = tree.count_nodes() - 1  # 去掉根节点

    # ---- 4. 生成各模块 ----
    depth = config.mind_map_depth
    modules = config.output_modules

    # 课程摘要
    summary = CourseSummary(
        course_name=course.course_name,
        knowledge_point_count=max(0, total_kp),
        high_freq_count=sum(
            1 for n in tree.iter_nodes()
            if n.importance == "high" and n.level > 0
        ),
    )

    # 思维导图
    mind_map = None
    if "mind_map" in modules:
        mermaid_str = generate_mermaid(tree, max_depth=depth)
        json_tree = generate_json_tree(tree, max_depth=depth)
        mind_map = MindMapOutput(
            mermaid_string=mermaid_str,
            json_structure=json_tree,
        )

    # 复习资料
    review_materials = ReviewMaterials()
    if "basic_concepts" in modules:
        concepts = generate_basic_concepts(tree)
        review_materials.basic_concepts = [
            _to_knowledge_point(c) for c in concepts
        ]
    if "high_freq_points" in modules:
        hf_points = generate_high_freq_points(tree)
        review_materials.high_freq_points = [
            _to_high_freq_point(h) for h in hf_points
        ]
    if "error_prone" in modules:
        errors = generate_error_prone(tree, parsed_docs)
        review_materials.error_prone_summary = [
            _to_error_prone_item(e) for e in errors
        ]

    # ---- 5. 溯源映射 ----
    source_trace = _build_source_trace(tree)

    # ---- 6. 组装输出 ----
    output = make_output(
        course_summary=summary,
        mind_map=mind_map,
        review_materials=review_materials,
        source_trace=source_trace,
    )

    # 如果有部分文件失败，修改 code 和 message
    if failed_files:
        output.code = ErrorCode.PARTIAL_PARSE_FAILURE
        output.message = f"部分素材解析失败: {failed_files}"
        output.data["failed_files"] = failed_files

    # 如果内容过少
    if sum(d.total_chars for d in parsed_docs) < 500:
        output.message += " | 提示：素材内容较少（<500字），输出为基础框架"

    return output.model_dump()


# ---- 辅助转换函数 ----

def _to_knowledge_point(item: dict) -> KnowledgePoint:
    return KnowledgePoint(
        id=generate_kp_id(item["name"]),
        name=item["name"],
        content=item.get("content", ""),
        level=item.get("level", 1),
        importance=item.get("importance", "normal"),
        sources=_convert_sources(item.get("sources", [])),
    )


def _to_high_freq_point(item: dict) -> HighFreqPoint:
    return HighFreqPoint(
        name=item["name"],
        frequency=item.get("frequency", "中频"),
        core_content=item.get("core_content", ""),
        question_types=item.get("question_types", []),
        sources=_convert_sources(item.get("sources", [])),
    )


def _to_error_prone_item(item: dict) -> ErrorProneItem:
    return ErrorProneItem(
        name=item["name"],
        type=item.get("type", "易错"),
        description=item.get("description", ""),
        comparison=item.get("comparison"),
        sources=_convert_sources(item.get("sources", [])),
    )


def _convert_sources(raw: list[dict]) -> list[SourceInfo]:
    result = []
    for s in raw:
        try:
            result.append(SourceInfo(
                file_name=s.get("file_name", ""),
                page=s.get("page"),
                slide=s.get("slide"),
                paragraph=s.get("paragraph"),
                priority=s.get("priority", "normal"),
            ))
        except Exception:
            continue
    return result


def _build_source_trace(tree) -> dict[str, list[dict]]:
    """构建知识点 ID → 来源映射"""
    trace: dict[str, list[dict]] = {}
    for node in tree.iter_nodes():
        kp_id = generate_kp_id(node.name)
        trace[kp_id] = node.sources
    return trace
