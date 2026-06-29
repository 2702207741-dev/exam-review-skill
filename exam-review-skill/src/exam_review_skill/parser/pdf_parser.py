"""
PDF 解析器

使用 pdfplumber 按页提取文本，尽量保留段落换行与标题结构。
识别扫描版 PDF 并给出提示。
"""

from __future__ import annotations

from .models import ParsedDocument


def parse_pdf(file_path: str, priority: str = "normal") -> ParsedDocument:
    """解析 PDF 文件，返回 ParsedDocument"""
    doc = ParsedDocument(
        file_path=file_path,
        file_type="pdf",
        priority=priority,
    )

    try:
        import pdfplumber
    except ImportError:
        doc.parse_errors.append("pdfplumber 未安装，请运行: pip install pdfplumber")
        return doc

    try:
        with pdfplumber.open(file_path) as pdf:
            doc.total_pages = len(pdf.pages)

            # 检测是否为扫描版
            if _is_scanned_pdf(pdf):
                doc.parse_errors.append(
                    "检测到该 PDF 可能为扫描版，暂不支持 OCR 解析，建议提供文本版素材"
                )
                return doc

            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text:
                    continue

                # 按行分割，推断段落与标题
                lines = text.split("\n")
                for line in lines:
                    stripped = line.strip()
                    if not stripped:
                        continue

                    # 推断层级
                    level = _infer_level_from_line(stripped, lines)

                    # 推断是否为重点
                    is_important = _is_likely_important(stripped)

                    doc.add_paragraph(
                        stripped,
                        level=level,
                        is_important=is_important,
                        page=page_num,
                    )

    except Exception as e:
        doc.parse_errors.append(f"PDF 解析失败: {e}")

    return doc


def _is_scanned_pdf(pdf) -> bool:
    """简单检测是否为扫描版 PDF"""
    total_chars = 0
    pages_to_check = min(3, len(pdf.pages))
    for page in pdf.pages[:pages_to_check]:
        text = page.extract_text()
        if text:
            total_chars += len(text.strip())
    # 前几页总字符数少于 200 → 很可能是扫描版
    return total_chars < 200


def _infer_level_from_line(line: str, all_lines: list[str]) -> int:
    """从行的特征推断标题层级"""
    stripped = line.strip()

    # 数字+点 / 中文数字+、→ 标题
    if any(stripped.startswith(p) for p in ("第", "一、", "二、", "三、",
            "四、", "五、", "六、", "七、", "八、", "九、", "十、")):
        return 1

    import re
    if re.match(r"^\d+[\.\、\)]", stripped):
        return 2
    if re.match(r"^\d+\.\d+", stripped):
        return 3

    # 短文本（<20字）+ 无标点结尾 → 可能是标题
    if len(stripped) < 20 and not stripped.endswith(("。", "，", "；")):
        # 相对于前一行，判断是否独立
        return 1

    return 0


def _is_likely_important(text: str) -> bool:
    """根据关键词推断文本是否为重要内容"""
    keywords = ["定义", "定理", "公式", "注意", "重点", "关键", "总结",
                "核心", "考点", "必考", "高频", "重要"]
    return any(kw in text for kw in keywords)
