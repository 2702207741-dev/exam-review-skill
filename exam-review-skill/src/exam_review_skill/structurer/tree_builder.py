"""
知识体系结构化模块

从 ParsedDocument 列表构建知识树，支持多素材合并、重要度评分。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class KnowledgeNode:
    """知识树节点"""
    name: str
    level: int = 1
    importance: str = "normal"      # high / normal / low
    children: list[KnowledgeNode] = field(default_factory=list)
    content_items: list[str] = field(default_factory=list)  # 正文碎片
    sources: list[dict] = field(default_factory=list)
    parent: KnowledgeNode | None = None

    def add_child(self, child: KnowledgeNode) -> None:
        child.parent = self
        self.children.append(child)

    def find_child(self, name: str) -> KnowledgeNode | None:
        for c in self.children:
            if c.name == name:
                return c
        return None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "level": self.level,
            "importance": self.importance,
            "children": [c.to_dict() for c in self.children],
            "content_items": self.content_items,
            "sources": self.sources,
        }

    def count_nodes(self) -> int:
        return 1 + sum(c.count_nodes() for c in self.children)

    def iter_nodes(self):
        """深度优先遍历所有节点"""
        yield self
        for c in self.children:
            yield from c.iter_nodes()


def build_knowledge_tree(parsed_docs: list) -> KnowledgeNode:
    """
    从多个 ParsedDocument 构建合并后的知识树。

    算法：
    1. 每个文档独立构建子树
    2. 同名称节点合并内容
    3. 高优先级素材内容覆盖低优先级
    4. 计算综合重要度
    """
    root = KnowledgeNode(name="ROOT", level=0)

    priority_weight = {"high": 3, "normal": 2, "low": 1}

    for doc in parsed_docs:
        if doc.is_empty:
            continue
        sub_root = _build_single_tree(doc)
        _merge_trees(root, sub_root, doc.priority, priority_weight)

    # 如果根节点只有一个孩子，提升它
    if len(root.children) == 1:
        return root.children[0]

    return root


def _build_single_tree(doc) -> KnowledgeNode:
    """从单个文档构建知识树"""
    root = KnowledgeNode(name=doc.file_path.split("/")[-1].split("\\")[-1], level=0)
    stack: list[KnowledgeNode] = [root]
    importance_counter: dict[str, int] = {}

    for para in doc.paragraphs:
        node = KnowledgeNode(
            name=_trim_node_name(para.text),
            level=para.level,
            importance="high" if para.is_important else "normal",
            sources=[{
                "file_name": doc.file_path,
                "page": para.page,
                "slide": para.slide,
                "paragraph": para.para_index,
                "priority": doc.priority,
            }],
        )

        if para.level > 0:
            # 标题行 → 创建/找到对应层级节点
            _place_heading_node(root, stack, node, para.level)
            # 统计出现频次
            importance_counter[node.name] = importance_counter.get(node.name, 0) + 1
        else:
            # 正文行 → 追加到当前节点的 content_items
            if stack:
                stack[-1].content_items.append(para.text)

    # 计算重要度
    _compute_importance(root, importance_counter, doc)

    return root


def _place_heading_node(root: KnowledgeNode, stack: list[KnowledgeNode],
                         node: KnowledgeNode, level: int) -> None:
    """将标题节点放入树中正确位置"""
    # 弹出比当前层级更深或同级的节点
    while len(stack) > 1 and stack[-1].level >= level:
        stack.pop()

    # 如果栈顶是同名节点，合并内容
    existing = stack[-1].find_child(node.name)
    if existing:
        existing.content_items.extend(node.content_items)
        existing.sources.extend(node.sources)
        stack.append(existing)
    else:
        stack[-1].add_child(node)
        stack.append(node)


def _merge_trees(target: KnowledgeNode, source: KnowledgeNode,
                  priority: str, weight_map: dict) -> None:
    """将 source 树合并到 target 树"""
    for src_child in source.children:
        tgt_child = target.find_child(src_child.name)
        if tgt_child:
            # 合并内容：高优先级覆盖
            if weight_map.get(priority, 2) >= weight_map.get("normal", 2):
                tgt_child.content_items = src_child.content_items + tgt_child.content_items
            else:
                tgt_child.content_items.extend(src_child.content_items)
            tgt_child.sources.extend(src_child.sources)
            _merge_trees(tgt_child, src_child, priority, weight_map)
        else:
            target.add_child(src_child)


def _compute_importance(root: KnowledgeNode, counter: dict,
                         doc) -> None:
    """递归计算节点重要度"""
    for child in root.children:
        freq = counter.get(child.name, 0)
        is_marked = child.importance == "high"

        if freq >= 3 or is_marked:
            child.importance = "high"
        elif freq >= 2:
            child.importance = "normal"
        else:
            child.importance = "low"

        _compute_importance(child, counter, doc)


def _trim_node_name(text: str, max_len: int = 60) -> str:
    """精简节点名称"""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def get_top_percent_nodes(root: KnowledgeNode, percent: float = 0.3) -> list[KnowledgeNode]:
    """获取重要度前 N% 的节点"""
    all_nodes = list(root.iter_nodes())
    # 按重要度排序
    importance_order = {"high": 3, "normal": 2, "low": 1}
    sorted_nodes = sorted(all_nodes,
        key=lambda n: (
            importance_order.get(n.importance, 0),
            len(n.content_items),
        ),
        reverse=True,
    )
    count = max(1, int(len(sorted_nodes) * percent))
    return sorted_nodes[:count]
