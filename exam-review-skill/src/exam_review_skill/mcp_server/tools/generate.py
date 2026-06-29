"""
MCP Tool: generate_questions

为指定知识点生成练习题。
"""

from __future__ import annotations

import json


def generate_questions_tool(knowledge_point: str,
                              question_type: str = "choice",
                              count: int = 3) -> str:
    """
    MCP Tool: generate_questions

    Args:
        knowledge_point: 知识点名称
        question_type: choice / fill / short_answer
        count: 题目数量

    Returns:
        JSON 字符串
    """
    try:
        from ...llm import generate_questions

        kp = {
            "name": knowledge_point,
            "content": "",
            "importance": "normal",
        }

        questions = generate_questions(kp, count=count, question_type=question_type)

        return json.dumps({
            "code": 0,
            "knowledge_point": knowledge_point,
            "questions": questions,
            "total": len(questions),
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "code": 500,
        }, ensure_ascii=False)
