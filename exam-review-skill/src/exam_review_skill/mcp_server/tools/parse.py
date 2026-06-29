"""
MCP Tool: parse_material

解析单个学习素材，返回结构化知识点。
"""

from __future__ import annotations

import json


def parse_material_tool(file_path: str, file_type: str,
                         analysis_mode: str = "llm") -> str:
    """
    MCP Tool: parse_material

    Args:
        file_path: 素材文件路径
        file_type: pptx/docx/pdf/txt/md
        analysis_mode: llm / rule

    Returns:
        JSON 字符串
    """
    try:
        from ...parser import parse_material
        from ...llm import chunk_from_parsed_doc, analyze_chunks, run_rule_fallback

        # 1. 解析文件
        doc = parse_material(file_path, file_type)

        if doc.is_empty:
            return json.dumps({
                "error": "素材内容为空",
                "code": 1003,
            }, ensure_ascii=False)

        # 2. 分析
        if analysis_mode == "llm":
            chunked = chunk_from_parsed_doc(doc)
            result = analyze_chunks(chunked)
            if result.get("analysis_mode") == "unavailable":
                result = run_rule_fallback([doc])
        else:
            result = run_rule_fallback([doc])

        return json.dumps({
            "code": 0,
            "file_path": file_path,
            "knowledge_points": result.get("knowledge_points", []),
            "relationships": result.get("relationships", []),
            "analysis_mode": result.get("analysis_mode", "unknown"),
            "total_kps": len(result.get("knowledge_points", [])),
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "code": 1002,
        }, ensure_ascii=False)
