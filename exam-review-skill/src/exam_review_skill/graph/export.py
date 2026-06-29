"""
知识图谱导出

支持 D3.js HTML、JSON、NetworkX 格式导出。
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import KnowledgeGraph
from .query import get_statistics


_TEMPLATE_DIR = Path(__file__).parent / "templates"


def export_d3_html(kg: KnowledgeGraph, output_path: str | None = None) -> str:
    """
    导出 D3.js 力导向图 HTML 文件。

    Args:
        kg: 知识图谱
        output_path: 输出文件路径（可选，None 则返回 HTML 字符串）

    Returns:
        HTML 字符串
    """
    template_path = _TEMPLATE_DIR / "graph.html"
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
    else:
        template = _generate_inline_template()

    # 注入图谱数据
    graph_data = {
        "nodes": [n.to_dict() for n in kg.nodes.values()],
        "edges": [e.to_dict() for e in kg.edges],
        "stats": get_statistics(kg),
        "course_name": kg.course_name,
    }
    graph_json = json.dumps(graph_data, ensure_ascii=False)

    html = template.replace(
        "/* GRAPH_DATA_PLACEHOLDER */",
        f"const GRAPH_DATA = {graph_json};",
    )

    if output_path:
        Path(output_path).write_text(html, encoding="utf-8")

    return html


def export_json(kg: KnowledgeGraph, output_path: str | None = None) -> dict:
    """导出原始 JSON"""
    data = {
        "course_name": kg.course_name,
        "nodes": [n.to_dict() for n in kg.nodes.values()],
        "edges": [e.to_dict() for e in kg.edges],
        "stats": get_statistics(kg),
    }
    if output_path:
        Path(output_path).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return data


def _generate_inline_template() -> str:
    """生成内联 D3.js 模板"""
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>知识图谱 - GRAPH_COURSE_NAME</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0a0e27; color: #e0e0e0; font-family: -apple-system, sans-serif; overflow: hidden; }
#graph { width: 100vw; height: 100vh; }
.link { stroke-opacity: 0.6; }
.link text { fill: #aaa; font-size: 10px; }
.node circle { stroke: #1a1a3e; stroke-width: 2px; cursor: pointer; }
.node text { font-size: 12px; pointer-events: none; }
.legend { position: fixed; top: 20px; right: 20px; background: rgba(10,14,39,0.9); border: 1px solid #333; border-radius: 8px; padding: 12px; font-size: 12px; z-index: 10; }
.legend-item { display: flex; align-items: center; margin: 4px 0; }
.legend-color { width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
.search { position: fixed; top: 20px; left: 20px; z-index: 10; }
.search input { padding: 8px 12px; border-radius: 6px; border: 1px solid #555; background: rgba(10,14,39,0.9); color: #e0e0e0; width: 200px; }
.tooltip { position: fixed; background: rgba(10,14,39,0.95); border: 1px solid #ffd54f; border-radius: 8px; padding: 12px; max-width: 300px; display: none; z-index: 100; font-size: 13px; }
.stats { position: fixed; bottom: 20px; left: 20px; background: rgba(10,14,39,0.9); border: 1px solid #333; border-radius: 8px; padding: 10px; font-size: 11px; z-index: 10; }
</style>
</head>
<body>
<div class="search"><input type="text" id="searchInput" placeholder="搜索知识点..." /></div>
<div class="legend" id="legend"></div>
<div class="stats" id="stats"></div>
<div class="tooltip" id="tooltip"></div>
<svg id="graph"></svg>

<script>
/* GRAPH_DATA_PLACEHOLDER */

const svg = d3.select("#graph");
const width = window.innerWidth;
const height = window.innerHeight;
const tooltip = d3.select("#tooltip");

const colorMap = {};
GRAPH_DATA.nodes.forEach(n => { colorMap[n.id] = n.color; });

// 图例
const legend = d3.select("#legend");
const typeColors = [...new Set(GRAPH_DATA.nodes.map(n => n.type))].map(t => ({
    type: t, color: GRAPH_DATA.nodes.find(n => n.type === t)?.color || '#666'
}));
legend.html('<b>图例</b>' + typeColors.map(t =>
    `<div class="legend-item"><div class="legend-color" style="background:${t.color}"></div>${t.type}</div>`
).join(''));

// 统计
const stats = GRAPH_DATA.stats || {};
d3.select("#stats").html(
    `节点: ${stats.total_nodes || GRAPH_DATA.nodes.length} | 边: ${stats.total_edges || GRAPH_DATA.edges.length}`
);

// 力导向图
const simulation = d3.forceSimulation(GRAPH_DATA.nodes)
    .force("link", d3.forceLink(GRAPH_DATA.edges).id(d => d.id).distance(100))
    .force("charge", d3.forceManyBody().strength(-300))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(d => d.radius + 5));

const g = svg.append("g");

const link = g.append("g").selectAll("line")
    .data(GRAPH_DATA.edges).join("line")
    .attr("stroke", d => d.color)
    .attr("stroke-dasharray", d => d.dash || "")
    .attr("stroke-width", d => 1 + d.weight * 3)
    .attr("stroke-opacity", 0.6);

const node = g.append("g").selectAll("g")
    .data(GRAPH_DATA.nodes).join("g")
    .attr("class", "node")
    .call(d3.drag()
        .on("start", (event, d) => { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
        .on("end", (event, d) => { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; })
    );

node.append("circle")
    .attr("r", d => d.radius)
    .attr("fill", d => d.color)
    .on("mouseover", (event, d) => {
        tooltip.style("display", "block")
            .html(`<b>${d.name}</b><br>类型: ${d.type}<br>重要度: ${d.importance}<br>${(d.content||'').slice(0,100)}`)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 10) + "px");
    })
    .on("mouseout", () => tooltip.style("display", "none"))
    .on("dblclick", (event, d) => {
        // 双击聚焦
        simulation.force("center", d3.forceCenter(d.x, d.y));
        simulation.alpha(1).restart();
    });

node.append("text")
    .text(d => d.name.length > 12 ? d.name.slice(0,11) + '..' : d.name)
    .attr("dy", d => d.radius + 14)
    .attr("text-anchor", "middle")
    .attr("fill", "#ccc");

simulation.on("tick", () => {
    link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
    node.attr("transform", d => `translate(${d.x},${d.y})`);
});

// 搜索
d3.select("#searchInput").on("input", function() {
    const kw = this.value.toLowerCase();
    node.select("circle")
        .attr("stroke", d => d.name.toLowerCase().includes(kw) ? "#ffd54f" : "#1a1a3e")
        .attr("stroke-width", d => d.name.toLowerCase().includes(kw) ? 3 : 2);
});

window.addEventListener("resize", () => {
    simulation.force("center", d3.forceCenter(window.innerWidth / 2, window.innerHeight / 2));
    simulation.alpha(1).restart();
});
</script>
</body>
</html>""".replace("GRAPH_COURSE_NAME", "{{course_name}}")
