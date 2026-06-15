"""动态导入 chart_core.py 中的 draw_chart 函数。"""

from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, Tuple


def import_draw_chart(core_path: str | Path) -> Callable[[Dict[str, Any]], Any]:
    """
    从 chart_core.py 动态导入 draw_chart(config)。

    导入前临时将项目根目录加入 sys.path，以支持项目内 helper.py 等辅助模块。
    """
    file_path = Path(core_path).resolve()
    if not file_path.is_file():
        raise FileNotFoundError(f"绘图核心文件不存在: {file_path}")

    project_root = str(file_path.parent)
    module_name = f"chart_core_{file_path.parent.name}_{id(file_path)}"

    if module_name in sys.modules:
        del sys.modules[module_name]

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
        raise ImportError(
            f"加载绘图核心文件失败: {exc}\n\n{tb}"
        ) from exc
    finally:
        if path_added and project_root in sys.path:
            sys.path.remove(project_root)

    draw_chart = getattr(module, "draw_chart", None)
    if draw_chart is None or not callable(draw_chart):
        raise AttributeError(f"{file_path.name} 中必须定义 draw_chart(config) 函数")

    return draw_chart
