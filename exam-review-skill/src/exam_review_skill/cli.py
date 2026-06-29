#!/usr/bin/env python3
"""
Exam Review Skill CLI v2.0

Usage:
    exam-review input.json                    # 从 JSON 文件读取输入
    exam-review input.json -o output.json     # 指定输出文件
    exam-review --demo                        # 运行内置示例
    exam-review --mcp                         # 启动 MCP Server
    exam-review --console                     # 启动 Quick Console (Gradio)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import click

from exam_review_skill.main import run
from exam_review_skill.utils import load_json, save_json


@click.command()
@click.argument("input_file", required=False)
@click.option("-o", "--output", help="输出 JSON 文件路径")
@click.option("--demo", is_flag=True, help="运行内置示例")
@click.option("--mcp", is_flag=True, help="启动 MCP Server (stdio 模式)")
@click.option("--console", is_flag=True, help="启动 Quick Console (Gradio Web UI)")
@click.option("--port", default=7860, help="Quick Console 端口 (默认 7860)")
@click.option("--pretty", is_flag=True, help="美化输出")
@click.version_option(version="2.0.0", prog_name="exam-review")
def cli(input_file: str | None, output: str | None,
        demo: bool, mcp: bool, console: bool,
        port: int, pretty: bool) -> None:
    """
    Exam Review Skill v2.0 — 期末复习知识整理

    输入：标准 JSON 格式的复习请求（见 docs/api_reference.md）
    输出：结构化复习资料 JSON + 知识图谱 HTML
    """
    if mcp:
        _run_mcp()
        return

    if console:
        _run_console(port)
        return

    if demo:
        _run_demo(output, pretty)
        return

    if not input_file:
        click.echo("请提供输入 JSON 文件，或使用 --demo / --mcp / --console", err=True)
        sys.exit(1)

    # 读取输入
    try:
        input_data = load_json(input_file)
    except FileNotFoundError:
        click.echo(f"文件不存在: {input_file}", err=True)
        sys.exit(1)
    except json.JSONDecodeError as e:
        click.echo(f"JSON 解析失败: {e}", err=True)
        sys.exit(1)

    # 执行
    click.echo(f"正在处理: {input_data.get('course_info', {}).get('course_name', '未知课程')} ...")
    result = run(input_data)

    # 输出
    indent = 2 if pretty else None
    json_str = json.dumps(result, ensure_ascii=False, indent=indent)

    if output:
        save_json(result, output)
        click.echo(f"结果已保存至: {output}")
    else:
        click.echo(json_str)

    # 状态提示
    code = result.get("code", -1)
    mode = result.get("data", {}).get("analysis_mode", "rule")
    if code == 0:
        click.echo(f"\n[OK] 处理成功 ({mode}模式) - "
                   f"{result['data'].get('course_summary', {}).get('knowledge_point_count', 0)} 个知识点")
    else:
        click.echo(f"\n[WARN] 处理完成 (code={code}): {result.get('message', '')}")


def _run_demo(output: str | None, pretty: bool) -> None:
    """运行内置示例"""
    _pkg_dir = os.path.dirname(os.path.abspath(__file__))
    _demo_md = os.path.join(_pkg_dir, "..", "..", "examples", "demo_notes.md")
    demo_input = {
        "course_info": {
            "course_name": "Python 程序设计",
            "chapter_scope": "第1-3章",
            "education_level": "本科",
            "exam_type": "期末"
        },
        "materials": [
            {
                "file_path": os.path.abspath(_demo_md),
                "file_type": "md",
                "priority": "high"
            }
        ],
        "config": {
            "mind_map_depth": 3,
            "output_modules": ["mind_map", "basic_concepts", "high_freq_points", "error_prone"],
            "focus_preference": "均衡",
            "analysis_mode": "rule",
        }
    }

    click.echo("运行内置示例...")
    result = run(demo_input)

    indent = 2 if pretty else None
    json_str = json.dumps(result, ensure_ascii=False, indent=indent)

    if output:
        save_json(result, output)
        click.echo(f"结果已保存至: {output}")
    else:
        click.echo(json_str)


def _run_mcp() -> None:
    """启动 MCP Server"""
    click.echo("启动 MCP Server (stdio 模式)...")
    from exam_review_skill.mcp_server import serve
    serve()


def _run_console(port: int) -> None:
    """启动 Quick Console"""
    click.echo(f"启动 Quick Console → http://localhost:{port}")
    from exam_review_skill.console import launch
    launch(port=port)


if __name__ == "__main__":
    cli()
