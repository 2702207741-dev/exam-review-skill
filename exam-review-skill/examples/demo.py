#!/usr/bin/env python3
"""
Exam Review Skill — 快速运行示例

用法：
    cd exam-review-skill
    pip install -e .
    python examples/demo.py

或直接调用 API：
    from exam_review_skill import run
    result = run(input_data)
"""

import json
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from exam_review_skill.main import run
from exam_review_skill.utils import load_json, save_json


def main():
    """运行示例"""
    # 1. 加载输入
    input_file = Path(__file__).parent / "sample_input.json"
    print(f"📖 加载输入: {input_file}")
    input_data = load_json(str(input_file))

    course_name = input_data["course_info"]["course_name"]
    print(f"📚 课程: {course_name}")
    print(f"📄 素材数: {len(input_data['materials'])}")
    print()

    # 2. 执行处理
    print("🔄 正在处理...")
    result = run(input_data)

    # 3. 输出结果
    code = result["code"]
    message = result["message"]
    data = result.get("data", {})

    print(f"📊 状态: code={code}, {message}")
    print()

    # 课程摘要
    summary = data.get("course_summary", {})
    print(f"  知识点总数: {summary.get('knowledge_point_count', 0)}")
    print(f"  高频考点数: {summary.get('high_freq_count', 0)}")
    print()

    # 思维导图预览
    mind_map = data.get("mind_map", {})
    mermaid = mind_map.get("mermaid_string", "")
    if mermaid:
        print("🧠 思维导图 (Mermaid):")
        print(mermaid[:500])
        if len(mermaid) > 500:
            print("  ... (截断)")
        print()

    # 复习资料统计
    review = data.get("review_materials", {})
    basic = review.get("basic_concepts", [])
    hf = review.get("high_freq_points", [])
    errors = review.get("error_prone_summary", [])

    print(f"📝 基础概念: {len(basic)} 条")
    if basic:
        for item in basic[:3]:
            print(f"    - {item['name']} [{item.get('importance', 'normal')}]")

    print(f"🎯 高频考点: {len(hf)} 条")
    if hf:
        for item in hf[:3]:
            print(f"    - {item['name']} ({item.get('frequency', '?')})")

    print(f"⚠️ 易错点: {len(errors)} 条")
    if errors:
        for item in errors[:3]:
            print(f"    - {item['name']} [{item.get('type', '?')}]")

    print()

    # 4. 保存完整结果
    output_file = Path(__file__).parent / "sample_output.json"
    save_json(result, str(output_file))
    print(f"💾 完整结果已保存至: {output_file}")

    # 5. 导出 Markdown 思维导图
    if "mind_map" in input_data.get("config", {}).get("output_modules", []):
        from exam_review_skill.mindmap import export_markdown_mindmap
        from exam_review_skill.parser import parse_material
        from exam_review_skill.structurer import build_knowledge_tree

        # 重新构建树用于导出
        parsed = parse_material(
            str(Path(__file__).parent / "demo_notes.md"),
            "md",
            priority="high"
        )
        tree = build_knowledge_tree([parsed])
        md_map = export_markdown_mindmap(tree, max_depth=3)
        md_file = Path(__file__).parent / "mindmap_export.md"
        md_file.write_text(md_map, encoding="utf-8")
        print(f"🗺️  导图已导出至: {md_file}")

    print()
    print("✅ 示例运行完成！")


if __name__ == "__main__":
    main()
