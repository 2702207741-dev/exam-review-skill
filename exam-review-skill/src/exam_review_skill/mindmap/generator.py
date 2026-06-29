"""
思维导图生成模块

从知识树生成双格式思维导图：
1. Mermaid mindmap 语法字符串
2. 嵌套 JSON 节点结构
"""

from __future__ import annotations

from ..structurer.tree_builder import KnowledgeNode


def generate_mermaid(root: KnowledgeNode, max_depth: int = 3) -> str:
    """
    生成 Mermaid mindmap 语法字符串。

    Args:
        root: 知识树根节点
        max_depth: 最大展开深度

    Returns:
        完整的 Mermaid mindmap 语法
    """
    lines = ["```mermaid", "mindmap"]
    root_name = _sanitize_mermaid_text(root.name)
    lines.append(f"  root(({root_name}))")

    for child in root.children:
        _append_mermaid_node(lines, child, depth=1, max_depth=max_depth)

    lines.append("```")
    return "\n".join(lines)


def _append_mermaid_node(lines: list[str], node: KnowledgeNode,
                          depth: int, max_depth: int) -> None:
    """递归追加 Mermaid 节点"""
    if depth > max_depth:
        return

    indent = "  " * depth
    name = _sanitize_mermaid_text(node.name)

    # 按重要程度标记图标
    icon_map = {"high": "★★", "normal": "★", "low": ""}
    icon = icon_map.get(node.importance, "")
    label = f"{icon} {name}" if icon else name

    if depth == 1:
        lines.append(f"{indent}{label}")
    else:
        lines.append(f"{indent}{label}")

    for child in node.children:
        _append_mermaid_node(lines, child, depth + 1, max_depth)


def _sanitize_mermaid_text(text: str) -> str:
    """清理文本以兼容 Mermaid 语法（保留中文全角括号）"""
    # 仅移除 ASCII 括号等破坏 Mermaid 语法的字符
    for ch in ["[", "]", "{", "}", "<", ">", '"', "\\"]:
        text = text.replace(ch, "")
    # ASCII 圆括号也移除（Mermaid 用 () 做节点形状标记）
    text = text.replace("(", "").replace(")", "")
    return text[:50]  # 截断过长文本


def generate_json_tree(root: KnowledgeNode, max_depth: int = 3) -> dict:
    """
    生成嵌套 JSON 节点结构。

    Args:
        root: 知识树根节点
        max_depth: 最大展开深度

    Returns:
        嵌套 JSON 结构
    """
    return _node_to_json(root, current_depth=1, max_depth=max_depth)


def _node_to_json(node: KnowledgeNode, current_depth: int,
                   max_depth: int) -> dict:
    """递归转换节点为 JSON"""
    result = {
        "name": node.name,
        "level": current_depth,
        "importance": node.importance,
        "children": [],
        "sources": node.sources,
    }

    if current_depth < max_depth:
        for child in node.children:
            result["children"].append(
                _node_to_json(child, current_depth + 1, max_depth)
            )

    return result


def export_markdown_mindmap(root: KnowledgeNode, max_depth: int = 3) -> str:
    """
    导出为 Markdown 格式导图（嵌套列表）。

    Args:
        root: 知识树根节点
        max_depth: 最大展开深度

    Returns:
        Markdown 格式导图文本
    """
    lines = [f"# 思维导图：{root.name}", ""]
    for child in root.children:
        _append_md_list(lines, child, depth=1, max_depth=max_depth)
    return "\n".join(lines)


def _append_md_list(lines: list[str], node: KnowledgeNode,
                     depth: int, max_depth: int) -> None:
    """递归追加 Markdown 列表项"""
    if depth > max_depth:
        return

    indent = "  " * (depth - 1)
    imp = {"high": "**【必考】** ", "normal": "", "low": ""}
    suffix = {"high": "", "normal": "", "low": " *(了解)*"}
    prefix = imp.get(node.importance, "")
    postfix = suffix.get(node.importance, "")

    lines.append(f"{indent}- {prefix}{node.name}{postfix}")

    for child in node.children:
        _append_md_list(lines, child, depth + 1, max_depth)
