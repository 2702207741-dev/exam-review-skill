# 使用指南

## 目录

1. [基础用法](#基础用法)
2. [进阶场景](#进阶场景)
3. [模块配置](#模块配置)
4. [异常处理](#异常处理)
5. [集成到 Agent](#集成到-agent)

---

## 基础用法

### 场景一：单文件复习资料生成

你有一份 Markdown 笔记，想快速生成复习资料：

```python
from exam_review_skill import run

result = run({
    "course_info": {
        "course_name": "数据结构",
        "exam_type": "期末"
    },
    "materials": [
        {"file_path": "notes/数据结构.md", "file_type": "md", "priority": "high"}
    ],
    "config": {
        "mind_map_depth": 3,
        "output_modules": ["mind_map", "basic_concepts", "error_prone"]
    }
})

# 查看思维导图
print(result["data"]["mind_map"]["mermaid_string"])

# 查看易错点
for item in result["data"]["review_materials"]["error_prone_summary"]:
    print(f"⚠️ {item['name']}: {item['description']}")
```

### 场景二：多文件合并复习

你有课件 PPT + 教材 PDF + 笔记 MD，需要合并去重：

```python
result = run({
    "course_info": {"course_name": "操作系统", "exam_type": "期末"},
    "materials": [
        {"file_path": "slides/os-ch1.pptx", "file_type": "pptx", "priority": "normal"},
        {"file_path": "textbook/os-ch1.pdf", "file_type": "pdf", "priority": "high"},
        {"file_path": "notes/os-notes.md", "file_type": "md", "priority": "high"},
    ]
})

# 多来源知识点会在 sources 中列出全部来源
kp = result["data"]["review_materials"]["basic_concepts"][0]
for src in kp["sources"]:
    print(f"来源: {src['file_name']}")
```

---

## 进阶场景

### 控制思维导图深度

```python
config = {
    "mind_map_depth": 2,  # 只展开到二级知识点
    "output_modules": ["mind_map"]
}
```

### 按学段/考试类型调整

```python
course_info = {
    "course_name": "高等数学",
    "education_level": "本科",      # 影响知识点难度标记
    "exam_type": "期中"             # 影响复习范围
}
```

### 侧重特定内容类型

```python
config = {
    "focus_preference": "公式"  # 侧重公式提取
    # 可选: "概念", "例题", "定理证明", "均衡"
}
```

### 分阶段输出

```python
# 一轮复习：只要基础概念
config_round1 = {
    "output_modules": ["basic_concepts"]
}

# 二轮复习：只要高频考点
config_round2 = {
    "output_modules": ["high_freq_points"]
}

# 考前冲刺：只要易错点
config_sprint = {
    "output_modules": ["error_prone"]
}
```

---

## 模块配置

### output_modules 详解

| 模块名 | 输出内容 | 适用阶段 |
|--------|----------|----------|
| mind_map | Mermaid 导图 + JSON 结构 | 全程 |
| basic_concepts | 全量知识点定义 | 一轮复习 |
| high_freq_points | 高频考点 + 题型 | 二轮复习 |
| error_prone | 易错点 + 混淆对比 | 考前冲刺 |

### priority 策略

- `high`：教材、官方课件、核心笔记 → 优先保留
- `normal`：普通笔记、参考材料 → 补充内容
- `low`：扩展阅读、参考资料 → 仅当无冲突时采纳

---

## 异常处理

### 部分文件解析失败

```python
result = run({...})

if result["code"] == 3001:
    print(f"警告：以下文件解析失败: {result['data']['failed_files']}")
    # 仍然可以使用成功解析部分的结果
    print(f"已成功处理 {result['data']['course_summary']['knowledge_point_count']} 个知识点")
```

### 扫描版 PDF

```python
# 如果遇到扫描版 PDF，系统会提示
result = run({...})
if "扫描版" in result.get("message", ""):
    print("建议：将 PDF 转换为文本版或使用 OCR 工具预处理")
```

### 素材太少

```python
# 素材总字数 < 500 字，系统会降级输出
result = run({...})
if "素材内容较少" in result.get("message", ""):
    print("提示：建议补充更多学习素材以获得更完整的复习资料")
```

---

## 集成到 Agent

### 作为 Skill 函数调用

```python
# Agent 调用示例
def agent_exam_review(course_name: str, file_paths: list[str]) -> dict:
    materials = []
    for fp in file_paths:
        ext = fp.rsplit(".", 1)[-1].lower()
        materials.append({
            "file_path": fp,
            "file_type": ext,
            "priority": "high"
        })

    return run({
        "course_info": {
            "course_name": course_name,
            "exam_type": "期末"
        },
        "materials": materials
    })
```

### 结合 Mermaid 渲染

```python
# 取出 Mermaid 语法，渲染到前端
result = run({...})
mermaid_code = result["data"]["mind_map"]["mermaid_string"]

# 在 HTML 中渲染：
# <div class="mermaid">
# {mermaid_code}
# </div>
# <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
```

### 结合 JSON 导图做自定义可视化

```python
# 取出 JSON 结构用 D3.js 或 ECharts 做自定义可视化
tree_json = result["data"]["mind_map"]["json_structure"]

def render_custom_tree(node, depth=0):
    """递归渲染自定义树形图"""
    print("  " * depth + f"{node['name']} [{node['importance']}]")
    for child in node.get("children", []):
        render_custom_tree(child, depth + 1)

render_custom_tree(tree_json)
```

### 作为 LangChain / AutoGPT Tool

```python
from langchain.tools import tool

@tool
def exam_review_tool(input_json: str) -> str:
    """生成期末复习资料。输入为标准 JSON 字符串。"""
    import json
    from exam_review_skill import run
    data = json.loads(input_json)
    result = run(data)
    return json.dumps(result, ensure_ascii=False, indent=2)
```
