"""
配置结构迁移 — 将旧版 chart.width/dpi 等字段升级为统一结构。
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple


def normalize_config(config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    在内存中规范化配置结构，不修改原 dict。

    Returns
    -------
    (normalized_config, migration_notes)
    """
    cfg = deepcopy(config)
    notes: List[str] = []

    chart = cfg.get("chart")
    if isinstance(chart, dict):
        figure = cfg.setdefault("figure", {})
        export = cfg.setdefault("export", {})

        if "width" in chart:
            if "width" not in figure:
                figure["width"] = chart.pop("width")
                notes.append("已将 chart.width 迁移到 figure.width")
            else:
                chart.pop("width", None)

        if "height" in chart:
            if "height" not in figure:
                figure["height"] = chart.pop("height")
                notes.append("已将 chart.height 迁移到 figure.height")
            else:
                chart.pop("height", None)

        if "dpi" in chart:
            if "dpi" not in export:
                export["dpi"] = chart.pop("dpi")
                notes.append("已将 chart.dpi 迁移到 export.dpi")
            else:
                chart.pop("dpi", None)

    line_style = cfg.get("line_style")
    if isinstance(line_style, dict):
        if "line_width" in line_style and "width" not in line_style:
            line_style["width"] = line_style.pop("line_width")
            notes.append("已将 line_style.line_width 迁移到 line_style.width")

    if "export" not in cfg:
        cfg["export"] = {"dpi": 150, "transparent": False}
    else:
        export = cfg["export"]
        if "transparent" not in export:
            export["transparent"] = False

    font = cfg.get("font")
    if isinstance(font, dict):
        had_legacy = "zh_name" not in font
        from core.system_fonts import ensure_font_defaults

        ensure_font_defaults(font)
        if had_legacy:
            notes.append("已为 font 配置补充中/英/数字字体名称与路径字段")

    return cfg, notes


def is_legacy_structure(config: Dict[str, Any]) -> bool:
    """是否仍含旧版顶层字段（未持久化迁移）。"""
    chart = config.get("chart", {})
    if isinstance(chart, dict) and any(k in chart for k in ("width", "height", "dpi")):
        return True
    line_style = config.get("line_style", {})
    if isinstance(line_style, dict) and "line_width" in line_style:
        return True
    return False
