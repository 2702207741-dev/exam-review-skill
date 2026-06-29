"""
LLM Prompt 模板库

所有 prompt 集中管理，支持变量插值。
"""

from __future__ import annotations


# ============================================================
# Prompt 1: 知识层级提取
# ============================================================

EXTRACT_KNOWLEDGE_POINTS = """你是课程知识结构分析专家。分析以下课程内容，提取所有知识点。

对每个知识点标注：
- name: 知识点名称（精简，≤20字）
- level: 层级深度（1=章级，2=节级，3=小节，4=细节，5=原子概念）
- importance: 重要程度（high/normal/low）
- type: 类型（concept/definition/theorem/formula/example/skill）
- prerequisites: 前置依赖知识点名称列表（没有则为空数组）
- source_hint: 该知识点对应的原文片段（≤50字）

返回 JSON 格式：
{
  "knowledge_points": [
    {
      "name": "...",
      "level": 2,
      "importance": "high",
      "type": "definition",
      "prerequisites": ["..."],
      "source_hint": "..."
    }
  ]
}

课程内容：
{content}"""


# ============================================================
# Prompt 2: 关系发现
# ============================================================

DISCOVER_RELATIONSHIPS = """分析以下知识点之间的关系，输出所有关系边。

关系类型：
- PREREQUISITE: A 是 B 的前置知识（必须按顺序学）
- CONTAINS: A 包含 B（层级包含）
- SIMILAR_TO: A 与 B 概念相似
- CONFUSED_WITH: A 与 B 容易混淆
- DERIVES_FROM: A 由 B 推导而来

返回 JSON 格式：
{
  "relationships": [
    {
      "source": "知识点A名称",
      "target": "知识点B名称",
      "type": "PREREQUISITE",
      "weight": 0.9,
      "reason": "简短说明（≤30字）"
    }
  ]
}

知识点列表：
{knowledge_points}"""


# ============================================================
# Prompt 3: 智能出题
# ============================================================

GENERATE_QUESTIONS = """为以下知识点生成考试题。

要求：
- 生成 {count} 道题
- 题型：{question_type}
- 难度匹配重要度：{importance}
- 包含正确答案和解析

返回 JSON 格式：
{
  "questions": [
    {
      "type": "{question_type}",
      "question": "题干",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "answer": "正确答案",
      "explanation": "解析（为什么对/错）"
    }
  ]
}
注意：填空题和简答题无需 options 字段。

知识点：
名称：{name}
内容：{content}"""


# ============================================================
# Prompt 4: 知识点总结
# ============================================================

SUMMARIZE_CONCEPT = """用一段简洁的话（≤100字）总结以下知识点的核心内容。

知识点名称：{name}
原始内容：{content}

返回 JSON：
{
  "summary": "...",
  "key_points": ["要点1", "要点2", "要点3"]
}"""


# ---- Prompt 模板渲染 ----

def render_prompt(template: str, **kwargs) -> str:
    """渲染 prompt 模板，{key} 替换为对应值"""
    result = template
    for key, value in kwargs.items():
        placeholder = "{" + key + "}"
        if isinstance(value, (list, dict)):
            import json
            value = json.dumps(value, ensure_ascii=False, indent=2)
        result = result.replace(placeholder, str(value))
    return result
