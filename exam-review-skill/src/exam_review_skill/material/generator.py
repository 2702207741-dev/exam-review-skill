"""
复习资料生成模块

按期末复习三阶段自动生成对应内容：
1. 基础层（一轮复习）：全量核心概念、定义、公式、定理
2. 进阶层（二轮复习）：高频考点汇总
3. 冲刺层（考前速记）：易错点汇总、易混淆概念对比
"""

from __future__ import annotations

from ..structurer.tree_builder import KnowledgeNode, get_top_percent_nodes
from ..parser.models import ParsedDocument


def generate_basic_concepts(root: KnowledgeNode) -> list[dict]:
    """
    基础层：提取所有知识点的定义类/概念类内容。

    Returns:
        [{name, content, importance, sources}, ...]
    """
    results = []
    for node in root.iter_nodes():
        if node.level >= 2 or len(node.content_items) > 0:
            content = "\n".join(node.content_items[:20])  # 限制每个节点最多 20 条正文
            if content.strip():
                results.append({
                    "name": node.name,
                    "content": content,
                    "level": node.level,
                    "importance": node.importance,
                    "sources": node.sources,
                })
    return results


def generate_high_freq_points(root: KnowledgeNode) -> list[dict]:
    """
    进阶层：筛选重要度前 30% 的知识点，补充题型归纳。

    Returns:
        [{name, frequency, core_content, question_types, sources}, ...]
    """
    top_nodes = get_top_percent_nodes(root, percent=0.3)
    results = []

    question_type_hints = {
        "定义": ["名词解释", "简答题"],
        "定理": ["证明题", "判断题"],
        "公式": ["计算题", "应用题"],
        "概念": ["选择题", "填空题", "简答题"],
        "特点": ["简答题", "论述题"],
        "区别": ["辨析题", "简答题"],
        "分类": ["选择题", "填空题"],
        "步骤": ["简答题", "应用题"],
        "方法": ["应用题", "简答题"],
    }

    for node in top_nodes:
        content = "\n".join(node.content_items[:10])
        if not content.strip():
            continue

        # 推断常考题型：检查 node.name + content_items
        combined_text = node.name + " " + content
        q_types = []
        for kw, types in question_type_hints.items():
            if kw in combined_text:
                q_types.extend(types)
        # 去重 + 最多 3 种
        q_types = list(dict.fromkeys(q_types))[:3]
        if not q_types:
            q_types = ["简答题"]

        results.append({
            "name": node.name,
            "frequency": "高频" if node.importance == "high" else "中频",
            "core_content": content,
            "question_types": q_types[:3],
            "sources": node.sources,
        })

    return results


def generate_error_prone(root: KnowledgeNode, parsed_docs: list[ParsedDocument] | None = None) -> list[dict]:
    """
    冲刺层：自动识别易错点与易混淆概念。

    Returns:
        [{name, type, description, comparison, sources}, ...]
    """
    results = []
    error_keywords = ["注意", "误区", "易错", "陷阱", "容易", "小心",
                       "常见错误", "不要", "避免", "区分", "区别"]

    for node in root.iter_nodes():
        combined = node.name + "\n" + "\n".join(node.content_items)
        matched_kws = [kw for kw in error_keywords if kw in combined]

        if matched_kws:
            description = _extract_error_sentence(combined, matched_kws)
            if description:
                results.append({
                    "name": node.name,
                    "type": "易混淆" if any(k in matched_kws for k in ["区分", "区别"]) else "易错",
                    "description": description,
                    "comparison": None,
                    "sources": node.sources,
                })

    # 补充易混淆概念对比
    _add_confusion_pairs(results, root)

    return results


def _extract_error_sentence(text: str, keywords: list[str]) -> str:
    """从文本中提取包含易错关键词的句子"""
    import re
    sentences = re.split(r"[。；;\n]", text)
    for kw in keywords:
        for s in sentences:
            if kw in s and len(s) > 5:
                return s.strip()
    return ""


def _add_confusion_pairs(results: list[dict], root: KnowledgeNode) -> None:
    """检测相似概念并添加对比"""
    # 简单策略：找名称相似的兄弟节点
    for node in root.iter_nodes():
        if node.parent:
            siblings = [s for s in node.parent.children if s != node]
            for sib in siblings:
                if _is_similar(node.name, sib.name):
                    # 避免重复
                    existing_names = {r["name"] for r in results}
                    pair_name = f"{node.name} vs {sib.name}"
                    if pair_name not in existing_names and f"{sib.name} vs {node.name}" not in existing_names:
                        results.append({
                            "name": pair_name,
                            "type": "易混淆",
                            "description": f'"{node.name}" 与 "{sib.name}" 概念相近，需注意区分',
                            "comparison": f"左：{node.name}，右：{sib.name}",
                            "sources": node.sources + sib.sources,
                        })


def _is_similar(a: str, b: str, threshold: float = 0.65) -> bool:
    """基于 Jaccard 字符 bigram 的相似度检测"""
    if len(a) < 3 or len(b) < 3:
        return False

    def _bigrams(s: str) -> set:
        return {s[i:i+2] for i in range(len(s) - 1)}

    bg_a = _bigrams(a)
    bg_b = _bigrams(b)
    if not bg_a or not bg_b:
        return False

    intersection = len(bg_a & bg_b)
    union = len(bg_a | bg_b)
    jaccard = intersection / union

    # 额外约束：长度比不能差太大
    len_ratio = min(len(a), len(b)) / max(len(a), len(b))

    return jaccard >= threshold and len_ratio >= 0.5
