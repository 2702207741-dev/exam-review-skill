"""
Quick Console — 生成下载组件
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def generate_and_download(files_info: list[dict], course_name: str,
                           mind_map_depth: int, focus: str,
                           analysis_mode: str) -> tuple[str, str, str, str]:
    """
    生成完整复习资料并返回下载路径。

    Returns:
        (json_path, md_path, mermaid_path, html_graph_path)
    """
    if not files_info:
        return ("", "", "", "")

    try:
        from ...main import run
        from ...graph import build_graph_rule_fallback, export_d3_html
        from ...parser import parse_material
        from ...structurer import build_knowledge_tree
        from ...mindmap import export_markdown_mindmap
    except ImportError as e:
        return (f"Error: {e}", "", "", "")

    # 构建输入
    materials = []
    for fi in files_info:
        materials.append({
            "file_path": fi["path"],
            "file_type": fi["type"],
            "priority": "normal",
        })

    input_data = {
        "course_info": {
            "course_name": course_name or "未命名课程",
            "education_level": "本科",
            "exam_type": "期末",
        },
        "materials": materials,
        "config": {
            "mind_map_depth": mind_map_depth,
            "output_modules": ["mind_map", "basic_concepts", "high_freq_points", "error_prone"],
            "focus_preference": focus,
        },
    }

    result = run(input_data)

    # 保存 JSON
    output_dir = Path(tempfile.mkdtemp(prefix="exam_review_"))
    json_path = str(output_dir / "review_output.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Markdown 思维导图
    parsed_docs = [parse_material(fi["path"], fi["type"]) for fi in files_info]
    tree = build_knowledge_tree(parsed_docs)
    md_map = export_markdown_mindmap(tree, max_depth=mind_map_depth)
    md_path = str(output_dir / "mindmap.md")
    Path(md_path).write_text(md_map, encoding="utf-8")

    # Mermaid 字符串
    mermaid_str = result.get("data", {}).get("mind_map", {}).get("mermaid_string", "")
    mermaid_path = str(output_dir / "mindmap.mermaid")
    Path(mermaid_path).write_text(mermaid_str, encoding="utf-8")

    # D3.js 知识图谱 HTML
    try:
        from ...graph import build_graph_rule_fallback, export_d3_html
        kg = build_graph_rule_fallback(tree, course_name=course_name)
        html_path = str(output_dir / "knowledge_graph.html")
        export_d3_html(kg, html_path)
    except Exception:
        html_path = ""

    return (json_path, md_path, mermaid_path, html_path)
