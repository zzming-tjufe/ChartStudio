"""
数据键名工具 — 列名转 config key，并保证唯一（避免 A-B / A_B 等冲突）。
"""

from __future__ import annotations

import re
from typing import Set


def safe_key(name: str) -> str:
    """键名仅保留字母/数字/中文；连字符与下划线不参与区分（A-B 与 A_B 归一为 AB）。"""
    s = re.sub(r"[^\w\u4e00-\u9fff]", "", str(name))
    s = s.replace("_", "")
    return s if s else "col"


def unique_key(name: str, used: Set[str], *, reserved: Set[str] | None = None) -> str:
    reserved = reserved or set()
    base = safe_key(name)
    key = base
    n = 2
    while key in used or key in reserved:
        key = f"{base}_{n}"
        n += 1
    used.add(key)
    return key


def category_series_key(category: str) -> str:
    return f"bar_{safe_key(category)}"
