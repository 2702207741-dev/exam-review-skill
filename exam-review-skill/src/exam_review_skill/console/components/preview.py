"""
Quick Console — 解析预览组件
"""

from __future__ import annotations


def generate_preview(files_info: list[dict], course_name: str,
                      analysis_mode: str) -> tuple[str, str, str, str, str]:
    """
    预览解析结果。

    Returns:
        (mindmap_html, basic_table_html, hf_table_html, error_table_html, stats_text)
    """
    if not files_info:
        return ("", "", "", "", "请先上传文件")

    try:
        from ...parser import parse_material
        from ...llm import chunk_from_parsed_doc, analyze_chunks, run_rule_fallback
        from ...structurer import build_knowledge_tree
        from ...mindmap import generate_mermaid
        from ...material import (
            generate_basic_concepts, generate_high_freq_points, generate_error_prone,
        )
    except ImportError as e:
        return ("", "", "", "", f"导入失败: {e}")

    parsed_docs = []
    for fi in files_info:
        try:
            doc = parse_material(fi["path"], fi["type"])
            parsed_docs.append(doc)
        except Exception as e:
            pass

    if not parsed_docs:
        return ("", "", "", "", "所有文件解析失败")

    # 知识结构化
    tree = build_knowledge_tree(parsed_docs)

    # 思维导图
    mermaid = generate_mermaid(tree, max_depth=3)
    mermaid_html = f"<pre style='color:#e0e0e0;font-size:12px;line-height:1.6'>{mermaid}</pre>"

    # 基础概念
    concepts = generate_basic_concepts(tree)
    basic_rows = ""
    for c in concepts[:20]:
        imp_icon = {"high": "★★★", "normal": "★★", "low": "★"}.get(c.get("importance", "low"), "")
        basic_rows += f"<tr><td>{c['name']}</td><td>{imp_icon}</td><td style='max-width:300px;overflow:hidden'>{c.get('content','')[:100]}</td></tr>"

    basic_html = f"""
    <table style='width:100%;border-collapse:collapse;font-size:12px;color:#ccc'>
    <tr style='background:#1a1a3e'><th>知识点</th><th>重要度</th><th>内容摘要</th></tr>
    {basic_rows}
    </table>
    """

    # 高频考点
    hf = generate_high_freq_points(tree)
    hf_rows = ""
    for h in hf[:10]:
        hf_rows += f"<tr><td>{h['name']}</td><td>{h.get('frequency','?')}</td><td>{', '.join(h.get('question_types',[]))}</td></tr>"
    hf_html = f"""
    <table style='width:100%;border-collapse:collapse;font-size:12px;color:#ccc'>
    <tr style='background:#1a1a3e'><th>考点</th><th>考频</th><th>题型</th></tr>
    {hf_rows}
    </table>
    """

    # 易错点
    errors = generate_error_prone(tree, parsed_docs)
    err_rows = ""
    for e in errors[:10]:
        err_rows += f"<tr><td>{e['name']}</td><td>{e.get('type','?')}</td><td>{e.get('description','')[:80]}</td></tr>"
    error_html = f"""
    <table style='width:100%;border-collapse:collapse;font-size:12px;color:#ccc'>
    <tr style='background:#1a1a3e'><th>条目</th><th>类型</th><th>说明</th></tr>
    {err_rows}
    </table>
    """

    # 统计
    total_kp = tree.count_nodes() - 1
    stats = f"知识点: {total_kp} | 基础概念: {len(concepts)} | 高频: {len(hf)} | 易错: {len(errors)}"

    return (mermaid_html, basic_html, hf_html, error_html, stats)
