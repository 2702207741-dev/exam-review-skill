"""
智能出题

基于 LLM 为指定知识点生成考试题。
"""

from __future__ import annotations

from .client import get_client
from .prompts import GENERATE_QUESTIONS, render_prompt

QUESTION_TYPES = {
    "choice": "选择题（4个选项，单选）",
    "fill": "填空题",
    "short_answer": "简答题",
}


def generate_questions(
    knowledge_point: dict,
    count: int = 3,
    question_type: str = "choice",
) -> list[dict]:
    """
    为知识点生成题目。

    Args:
        knowledge_point: {name, content, importance}
        count: 题目数量
        question_type: choice / fill / short_answer

    Returns:
        题目列表 [{type, question, options?, answer, explanation}]
    """
    client = get_client()

    if not client.available:
        return _generate_rule_based(knowledge_point, count, question_type)

    type_desc = QUESTION_TYPES.get(question_type, question_type)
    prompt = render_prompt(
        GENERATE_QUESTIONS,
        count=count,
        question_type=type_desc,
        importance=knowledge_point.get("importance", "normal"),
        name=knowledge_point.get("name", ""),
        content=knowledge_point.get("content", knowledge_point.get("source_hint", "")),
    )

    messages = [
        {"role": "system", "content": "你是一个考试出题专家，只输出 JSON。"},
        {"role": "user", "content": prompt},
    ]

    try:
        result = client.chat_json(messages, temperature=0.7)
        if isinstance(result, dict):
            return result.get("questions", [])
    except Exception:
        pass

    return _generate_rule_based(knowledge_point, count, question_type)


def _generate_rule_based(kp: dict, count: int,
                          question_type: str) -> list[dict]:
    """离线出题（简单模板）"""
    name = kp.get("name", "知识点")
    content = kp.get("content", "")
    questions = []

    for i in range(count):
        if question_type == "choice":
            questions.append({
                "type": "choice",
                "question": f'下列关于"{name}"的说法，正确的是？',
                "options": [
                    f"A. {content[:50]}..." if content else f"A. {name}的定义",
                    f"B. {name}的另一种表述",
                    "C. 以上都对",
                    "D. 以上都不对",
                ],
                "answer": "C",
                "explanation": f"请参考教材中关于 {name} 的详细说明。",
            })
        elif question_type == "fill":
            questions.append({
                "type": "fill",
                "question": f'{name} 的核心内容是：______',
                "answer": content[:100] if content else "（请参考教材）",
                "explanation": f"该知识点要求掌握 {name} 的基本概念。",
            })
        else:
            questions.append({
                "type": "short_answer",
                "question": f'请简述 {name} 的主要内容。',
                "answer": content[:200] if content else "（请参考教材）",
                "explanation": f"该知识点要求理解并能够用自己的语言表述 {name}。",
            })

    return questions[:count]
