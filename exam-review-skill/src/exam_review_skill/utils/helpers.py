"""
工具函数模块
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def generate_kp_id(name: str, source: str = "") -> str:
    """生成知识点唯一 ID"""
    raw = f"{name}:{source}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def load_json(path: str) -> dict:
    """加载 JSON 文件"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: dict, path: str, indent: int = 2) -> None:
    """保存 JSON 文件"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def save_text(text: str, path: str) -> None:
    """保存文本文件"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
