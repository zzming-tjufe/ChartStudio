"""路径与项目名工具。"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Union

_INVALID_WIN_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_project_name(name: str) -> str:
    """清理项目文件夹名，去除 Windows 非法字符。"""
    s = str(name or "").strip()
    s = _INVALID_WIN_CHARS.sub("_", s)
    s = re.sub(r"\s+", " ", s).strip(" .")
    return s


def default_project_folder_name(template_id: str) -> str:
    """未填写项目名时的默认文件夹名。"""
    from core.template_registry import get_template_display_name

    base = sanitize_project_name(get_template_display_name(template_id)) or template_id
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base}_{ts}"


def resolve_project_root(
    parent_dir: Union[str, Path],
    project_name: str,
) -> Path:
    """父目录 + 项目名 → 项目根路径。"""
    parent = Path(parent_dir).expanduser().resolve()
    safe = sanitize_project_name(project_name)
    if not safe:
        raise ValueError("项目名称无效或为空")
    return parent / safe
