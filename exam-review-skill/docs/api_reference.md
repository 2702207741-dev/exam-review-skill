# API Reference

## 接口概述

Exam Review Skill 提供统一的 JSON 接口，Agent 通过标准化参数调用，获取结构化复习资料。

**输入协议版本**: v1.0
**输出协议版本**: v1.0

---

## 输入参数

### 顶层结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| course_info | CourseInfo | ✅ | 课程信息 |
| materials | Material[] | ✅ | 素材列表，至少 1 项 |
| config | Config | ❌ | 运行配置，有默认值 |

### CourseInfo

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| course_name | string | ✅ | — | 课程名称 |
| chapter_scope | string | ❌ | "全量" | 复习章节范围 |
| education_level | string | ❌ | "本科" | 学段：高中/本科/专科/研究生 |
| exam_type | string | ❌ | "期末" | 考试类型：期末/期中/补考/单元测 |

### Material

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| file_path | string | ✅ | — | 文件本地路径或 URL |
| file_type | string | ✅ | — | 格式：pptx/docx/pdf/txt/md |
| priority | string | ❌ | "normal" | 优先级：high/normal/low |

### Config

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| mind_map_depth | int | ❌ | 3 | 思维导图展开层级 (1-8) |
| output_modules | string[] | ❌ | ["mind_map", "basic_concepts", "high_freq_points", "error_prone"] | 要输出的模块 |
| focus_preference | string | ❌ | "均衡" | 侧重方向：概念/公式/例题/定理证明/均衡 |

---

## 输出结果

### 顶层结构

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 状态码，0=成功 |
| message | string | 执行状态描述 |
| data | object | 返回数据（结构见下） |

### data 结构

| 字段 | 类型 | 说明 |
|------|------|------|
| course_summary | CourseSummary | 课程摘要 |
| mind_map | MindMapOutput | 思维导图（仅当 output_modules 包含 mind_map） |
| review_materials | ReviewMaterials | 复习资料（按 output_modules 过滤） |
| source_trace | object | 知识点 ID → 来源列表映射 |
| failed_files | string[] | 解析失败的文件列表（仅部分失败时出现） |

### CourseSummary

| 字段 | 类型 | 说明 |
|------|------|------|
| course_name | string | 课程名称 |
| knowledge_point_count | int | 知识点总数 |
| high_freq_count | int | 高频考点数 |

### MindMapOutput

| 字段 | 类型 | 说明 |
|------|------|------|
| mermaid_string | string | Mermaid mindmap 完整语法 |
| json_structure | object | 嵌套 JSON 节点结构 |

### ReviewMaterials

| 字段 | 类型 | 说明 |
|------|------|------|
| basic_concepts | BasicConcept[] | 基础概念汇总 |
| high_freq_points | HighFreqPoint[] | 高频考点汇总 |
| error_prone_summary | ErrorProneItem[] | 易错点汇总 |

### BasicConcept

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 知识点唯一 ID |
| name | string | 知识点名称 |
| content | string | 概念内容 |
| level | int | 层级深度 |
| importance | string | 重要程度：high/normal/low |
| sources | SourceInfo[] | 来源列表 |

### HighFreqPoint

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 考点名称 |
| frequency | string | 考频描述 |
| core_content | string | 核心内容 |
| question_types | string[] | 常考题型 |
| sources | SourceInfo[] | 来源列表 |

### ErrorProneItem

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 条目名称 |
| type | string | "易错" 或 "易混淆" |
| description | string | 说明 |
| comparison | string|null | 对比说明（易混淆时） |
| sources | SourceInfo[] | 来源列表 |

### SourceInfo

| 字段 | 类型 | 说明 |
|------|------|------|
| file_name | string | 来源文件名 |
| page | int|null | 页码 |
| slide | int|null | 幻灯片号 |
| paragraph | int|null | 段落序号 |
| priority | string | 素材优先级 |

---

## 错误码

| 错误码 | 含义 | 处理建议 |
|--------|------|----------|
| 0 | 执行成功 | 正常使用返回数据 |
| 1001 | 文件格式不支持 | 检查 file_type 是否为支持格式 |
| 1002 | 文件损坏/无法读取 | 检查文件完整性 |
| 1003 | 素材内容为空 | 提供有效内容的素材 |
| 2001 | 参数缺失/格式错误 | 按本文档修正参数 |
| 3001 | 解析部分失败 | 检查 data.failed_files，修正失败文件 |

---

## 完整示例

### 输入

```json
{
  "course_info": {
    "course_name": "Python 程序设计",
    "chapter_scope": "第1-3章",
    "education_level": "本科",
    "exam_type": "期末"
  },
  "materials": [
    {
      "file_path": "notes/chapter1.md",
      "file_type": "md",
      "priority": "high"
    },
    {
      "file_path": "slides/lecture1.pptx",
      "file_type": "pptx",
      "priority": "normal"
    }
  ],
  "config": {
    "mind_map_depth": 3,
    "output_modules": ["mind_map", "basic_concepts", "high_freq_points", "error_prone"],
    "focus_preference": "均衡"
  }
}
```

### 输出

```json
{
  "code": 0,
  "message": "执行成功",
  "data": {
    "course_summary": {
      "course_name": "Python 程序设计",
      "knowledge_point_count": 25,
      "high_freq_count": 8
    },
    "mind_map": {
      "mermaid_string": "```mermaid\nmindmap\n  root((Python 程序设计))\n    基础语法\n      变量与类型\n      控制流\n    ...\n```",
      "json_structure": {
        "name": "Python 程序设计",
        "level": 1,
        "importance": "high",
        "children": [...]
      }
    },
    "review_materials": {
      "basic_concepts": [...],
      "high_freq_points": [...],
      "error_prone_summary": [...]
    },
    "source_trace": {
      "abc123": [{"file_name": "notes/chapter1.md", "paragraph": 3, "priority": "high"}]
    }
  }
}
```
