"""
MCP Server — Exam Review Skill

暴露 4 个 MCP tool 供 Claude Desktop / Agent 调用。

启动方式：
    exam-review-mcp          # stdio 模式
    python -m exam_review_skill.mcp_server.server   # 直接运行
"""

from __future__ import annotations

import json
import sys
from typing import Any


# ---- MCP Protocol 实现（简化版，无需外部依赖） ----

def _read_message() -> dict | None:
    """从 stdin 读取 JSON-RPC 消息"""
    try:
        line = sys.stdin.readline()
        if not line:
            return None
        return json.loads(line)
    except Exception:
        return None


def _write_message(msg: dict) -> None:
    """向 stdout 写入 JSON-RPC 消息"""
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _send_response(request_id: Any, result: Any) -> None:
    _write_message({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    })


def _send_error(request_id: Any, code: int, message: str) -> None:
    _write_message({
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    })


# ---- Tool 注册 ----

TOOLS = {
    "parse_material": {
        "description": "解析学习素材文件，提取结构化知识点",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "素材文件路径"},
                "file_type": {"type": "string", "description": "文件格式: pptx/docx/pdf/txt/md"},
                "analysis_mode": {"type": "string", "description": "分析模式: llm 或 rule", "default": "llm"},
            },
            "required": ["file_path", "file_type"],
        },
    },
    "generate_review": {
        "description": "一键生成期末复习全套资料（思维导图+三层复习资料+溯源）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "material_paths": {
                    "type": "array", "items": {"type": "string"},
                    "description": "素材文件路径列表",
                },
                "course_name": {"type": "string", "description": "课程名称"},
                "config": {"type": "object", "description": "配置（可选）"},
            },
            "required": ["material_paths", "course_name"],
        },
    },
    "query_knowledge_graph": {
        "description": "查询知识图谱（前置依赖/学习路径/相似概念/混淆对/搜索/统计/子图）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query_type": {
                    "type": "string",
                    "description": "查询类型: prerequisites/learning_path/similar/confusion/search/stats/subgraph",
                },
                "node_id": {"type": "string", "description": "节点 ID（部分查询需要）"},
                "keyword": {"type": "string", "description": "搜索关键词"},
                "depth": {"type": "integer", "description": "子图深度", "default": 1},
            },
            "required": ["query_type"],
        },
    },
    "generate_questions": {
        "description": "为指定知识点生成考试练习题",
        "inputSchema": {
            "type": "object",
            "properties": {
                "knowledge_point": {"type": "string", "description": "知识点名称"},
                "question_type": {
                    "type": "string",
                    "description": "题型: choice/fill/short_answer",
                    "default": "choice",
                },
                "count": {"type": "integer", "description": "题目数量", "default": 3},
            },
            "required": ["knowledge_point"],
        },
    },
}


def _handle_tool_call(name: str, arguments: dict) -> str:
    """分发 tool 调用"""
    if name == "parse_material":
        from .tools.parse import parse_material_tool
        return parse_material_tool(
            file_path=arguments["file_path"],
            file_type=arguments["file_type"],
            analysis_mode=arguments.get("analysis_mode", "llm"),
        )
    elif name == "generate_review":
        from .tools.review import generate_review_tool
        return generate_review_tool(
            material_paths=arguments["material_paths"],
            course_name=arguments["course_name"],
            config=arguments.get("config"),
        )
    elif name == "query_knowledge_graph":
        from .tools.query import query_graph_tool
        return query_graph_tool(
            query_type=arguments["query_type"],
            node_id=arguments.get("node_id", ""),
            keyword=arguments.get("keyword", ""),
            depth=arguments.get("depth", 1),
        )
    elif name == "generate_questions":
        from .tools.generate import generate_questions_tool
        return generate_questions_tool(
            knowledge_point=arguments["knowledge_point"],
            question_type=arguments.get("question_type", "choice"),
            count=arguments.get("count", 3),
        )
    else:
        return json.dumps({"error": f"Unknown tool: {name}"})


# ---- 主循环 ----

def serve() -> None:
    """启动 MCP Server (stdio 模式)"""
    import logging
    logging.basicConfig(level=logging.WARNING)

    while True:
        msg = _read_message()
        if msg is None:
            break

        method = msg.get("method", "")
        msg_id = msg.get("id")

        if method == "initialize":
            _send_response(msg_id, {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "exam-review-skill",
                    "version": "2.0.0",
                },
                "capabilities": {
                    "tools": {},
                },
            })

        elif method == "tools/list":
            _send_response(msg_id, {
                "tools": [
                    {"name": name, **info}
                    for name, info in TOOLS.items()
                ],
            })

        elif method == "tools/call":
            params = msg.get("params", {})
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})

            try:
                result_text = _handle_tool_call(tool_name, tool_args)
                _send_response(msg_id, {
                    "content": [
                        {"type": "text", "text": result_text},
                    ],
                })
            except Exception as e:
                _send_response(msg_id, {
                    "content": [
                        {"type": "text", "text": json.dumps({
                            "error": str(e),
                            "code": 500,
                        }, ensure_ascii=False)},
                    ],
                    "isError": True,
                })

        elif method == "notifications/initialized":
            pass  # 无需响应

        else:
            _send_error(msg_id, -32601, f"Method not found: {method}")


if __name__ == "__main__":
    serve()
