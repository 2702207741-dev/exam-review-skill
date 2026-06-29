"""
Quick Console — 文件上传组件
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def handle_upload(files: list) -> dict:
    """
    处理上传文件。

    Args:
        files: Gradio 上传的临时文件路径列表

    Returns:
        {
            "files": [{name, path, type, size}, ...],
            "total_files": N,
            "message": "状态信息"
        }
    """
    if not files:
        return {"files": [], "total_files": 0, "message": "请上传至少一个文件"}

    result_files = []
    for f in files:
        if hasattr(f, 'name'):
            file_name = os.path.basename(f.name)
            file_path = f.name
        elif isinstance(f, str):
            file_name = os.path.basename(f)
            file_path = f
        else:
            continue

        ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        supported = {"pptx", "docx", "pdf", "txt", "md"}
        if ext not in supported:
            continue

        size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        result_files.append({
            "name": file_name,
            "path": file_path,
            "type": ext,
            "size": f"{size / 1024:.1f} KB" if size > 1024 else f"{size} B",
        })

    return {
        "files": result_files,
        "total_files": len(result_files),
        "message": f"已上传 {len(result_files)} 个文件"
        if result_files else "未识别到支持的文件格式（支持: PPTX/DOCX/PDF/TXT/MD）",
    }
