"""
MCP Tool: generate_review

一键生成期末复习全套资料。
"""

from __future__ import annotations

import json


def generate_review_tool(material_paths: list[str],
                          course_name: str,
                          config: dict | None = None) -> str:
    """
    MCP Tool: generate_review

    Args:
        material_paths: 素材路径列表
        course_name: 课程名称
        config: 配置字典 (可选)

    Returns:
        JSON 字符串
    """
    if config is None:
        config = {}

    try:
        from ....main import run

        # 自动推断文件类型
        materials = []
        for fp in material_paths:
            ext = fp.rsplit(".", 1)[-1].lower() if "." in fp else "md"
            materials.append({
                "file_path": fp,
                "file_type": ext,
                "priority": "normal",
            })

        input_data = {
            "course_info": {
                "course_name": course_name,
                "education_level": config.get("education_level", "本科"),
                "exam_type": config.get("exam_type", "期末"),
            },
            "materials": materials,
            "config": {
                "mind_map_depth": config.get("mind_map_depth", 3),
                "output_modules": config.get("output_modules",
                    ["mind_map", "basic_concepts", "high_freq_points", "error_prone"]),
                "focus_preference": config.get("focus_preference", "均衡"),
            },
        }

        result = run(input_data)
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "code": 3001,
        }, ensure_ascii=False)
