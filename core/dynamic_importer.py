"""动态导入 chart_core.py 中的 draw_chart 函数。"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Dict


def _module_name_for_path(file_path: Path) -> str:
    digest = hashlib.sha256(str(file_path).encode("utf-8")).hexdigest()[:16]
    safe_parent = file_path.parent.name.replace("-", "_")
    return f"chart_core_{safe_parent}_{digest}"


def purge_chart_core_modules(keep: str | None = None) -> None:
    """清理已加载的 chart_core 动态模块，避免重载后仍用旧代码。"""
    for name in list(sys.modules.keys()):
        if name.startswith("chart_core_") and name != keep:
            del sys.modules[name]


def import_draw_chart(core_path: str | Path, *, purge_old: bool = True) -> Callable[[Dict[str, Any]], Any]:
    """
    从 chart_core.py 动态导入 draw_chart(config)。

    模块名基于文件绝对路径的稳定 hash，重载时清理旧模块。
    """
    file_path = Path(core_path).resolve()
    if not file_path.is_file():
        raise FileNotFoundError(f"绘图核心文件不存在: {file_path}")

    module_name = _module_name_for_path(file_path)
    if purge_old:
        purge_chart_core_modules(keep=None)
    elif module_name in sys.modules:
        del sys.modules[module_name]

    project_root = str(file_path.parent)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载模块: {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    path_added = False
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        path_added = True

    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        tb = traceback.format_exc()
        if module_name in sys.modules:
            del sys.modules[module_name]
        raise ImportError(f"加载绘图核心文件失败: {exc}\n\n{tb}") from exc
    finally:
        if path_added and project_root in sys.path:
            sys.path.remove(project_root)

    draw_chart = getattr(module, "draw_chart", None)
    if draw_chart is None or not callable(draw_chart):
        raise AttributeError(f"{file_path.name} 中必须定义 draw_chart(config) 函数")

    return draw_chart
