"""
配置结构迁移 — 将旧版 chart.width/dpi 等字段升级为统一结构。
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from core.constants import CHARTSTUDIO_VERSION, SCHEMA_VERSION
from core.layout import DEFAULT_LAYOUT


def ensure_schema_metadata(
    config: Dict[str, Any],
    template_id: str = "",
) -> Dict[str, Any]:
    """写入/补全 schema_version、template_id、chartstudio_version。"""
    config["schema_version"] = SCHEMA_VERSION
    if template_id and not config.get("template_id"):
        config["template_id"] = template_id
    if "chartstudio_version" not in config:
        config["chartstudio_version"] = CHARTSTUDIO_VERSION
    return config


def _ensure_layout(cfg: Dict[str, Any]) -> None:
    layout = cfg.get("layout")
    if not isinstance(layout, dict):
        layout = {}
        cfg["layout"] = layout
    for key, default in DEFAULT_LAYOUT.items():
        if key not in layout:
            layout[key] = default


def _ensure_export(cfg: Dict[str, Any], notes: List[str]) -> None:
    if "export" not in cfg:
        cfg["export"] = {"dpi": 150, "transparent": False, "bbox": "fixed"}
        notes.append("已补齐 export 段（dpi / transparent / bbox）")
        return

    export = cfg["export"]
    if not isinstance(export, dict):
        cfg["export"] = {"dpi": 150, "transparent": False, "bbox": "fixed"}
        notes.append("export 段无效，已重置为默认值")
        return

    if "dpi" not in export:
        export["dpi"] = 150
    if "transparent" not in export:
        export["transparent"] = False
    if "bbox" not in export:
        export["bbox"] = "fixed"
        notes.append("已为 export 补齐 bbox: fixed")


def normalize_config(
    config: Dict[str, Any],
    template_id: str = "",
) -> Tuple[Dict[str, Any], List[str]]:
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
            export = cfg.setdefault("export", {})
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

    _ensure_export(cfg, notes)
    _ensure_layout(cfg)

    if "annotations" not in cfg or not isinstance(cfg.get("annotations"), list):
        cfg["annotations"] = []
        if "annotations" in config and not isinstance(config.get("annotations"), list):
            notes.append("annotations 无效，已重置为空列表")

    font = cfg.get("font")
    if isinstance(font, dict):
        had_legacy = "zh_name" not in font
        from core.system_fonts import ensure_font_defaults

        ensure_font_defaults(font)
        if had_legacy:
            notes.append("已为 font 配置补充中/英/数字字体名称与路径字段")

    axes = cfg.get("axes")
    if isinstance(axes, dict):
        if "xlim" not in axes:
            axes["xlim"] = None
        if "ylim" not in axes:
            axes["ylim"] = None
        if "y_margin" not in axes:
            axes["y_margin"] = 0.05

    data_labels = cfg.get("data_labels")
    if isinstance(data_labels, dict):
        if "decimals" not in data_labels:
            data_labels["decimals"] = 1
        if "prefix" not in data_labels:
            data_labels["prefix"] = ""
        if "suffix" not in data_labels:
            data_labels["suffix"] = ""

    prev_schema = config.get("schema_version")
    ensure_schema_metadata(cfg, template_id=template_id)
    if prev_schema is not None and prev_schema != SCHEMA_VERSION:
        notes.append(f"已将 schema_version 从 {prev_schema} 升级到 {SCHEMA_VERSION}")

    return cfg, notes


def is_legacy_structure(config: Dict[str, Any]) -> bool:
    """是否仍含旧版顶层字段（未持久化迁移）。"""
    chart = config.get("chart", {})
    if isinstance(chart, dict) and any(k in chart for k in ("width", "height", "dpi")):
        return True
    line_style = config.get("line_style", {})
    if isinstance(line_style, dict) and "line_width" in line_style:
        return True
    if config.get("schema_version") != SCHEMA_VERSION:
        return True
    export = config.get("export", {})
    if isinstance(export, dict) and "bbox" not in export:
        return True
    if "layout" not in config:
        return True
    return False
