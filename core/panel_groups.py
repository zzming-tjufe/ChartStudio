"""
简洁模式面板 — 按图表调参逻辑分组展示控件。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import streamlit as st

from core.axis_panel import render_axis_limit_controls
from core.config_utils import find_paths, get_by_path, path_exists, set_by_path
from core.data_importer import render_data_panel
from core.semantic_widgets import render_canvas_size, render_field_widget, render_font_settings
from core.style_presets import render_style_presets

# 各模板允许的简洁模式分组（白名单）
TEMPLATE_GROUP_WHITELIST: Dict[str, Set[str]] = {
    "line_chart_basic": {
        "数据导入", "风格预设", "基础信息", "画布尺寸", "字体设置", "坐标轴", "图例", "线条样式",
        "颜色设置", "数据标签", "自定义文字位置", "导出设置",
    },
    "line_chart_report": {
        "数据导入", "风格预设", "基础信息", "画布尺寸", "字体设置", "坐标轴", "图例", "线条样式",
        "颜色设置", "数据标签", "自定义文字位置", "导出设置",
    },
    "line_chart": {
        "数据导入", "风格预设", "基础信息", "画布尺寸", "字体设置", "坐标轴", "图例", "线条样式",
        "颜色设置", "导出设置",
    },
    "bar_chart_basic": {
        "数据导入", "风格预设", "基础信息", "画布尺寸", "字体设置", "坐标轴", "图例", "柱状图样式",
        "颜色设置", "数据标签", "导出设置",
    },
    "horizontal_bar_chart": {
        "数据导入", "风格预设", "基础信息", "画布尺寸", "字体设置", "坐标轴", "柱状图样式",
        "颜色设置", "数据标签", "导出设置",
    },
    "heatmap_basic": {
        "数据导入", "风格预设", "基础信息", "画布尺寸", "字体设置", "坐标轴", "热力图样式", "导出设置",
    },
    "scatter_chart_basic": {
        "数据导入", "风格预设", "基础信息", "画布尺寸", "字体设置", "坐标轴", "图例", "散点样式",
        "颜色设置", "导出设置",
    },
}

SIMPLE_MODE_GROUPS: List[Dict[str, Any]] = [
    {"title": "数据导入", "data_import": True},
    {"title": "风格预设", "style_presets": True},
    {"title": "基础信息", "paths": ["chart.title", "chart.subtitle"]},
    {
        "title": "画布尺寸",
        "canvas_pair": ("figure.width", "figure.height"),
        "canvas_pair_alt": ("chart.width", "chart.height"),
    },
    {
        "title": "字体设置",
        "font_settings": True,
        "paths": [],
    },
    {
        "title": "坐标轴",
        "paths": [
            "axes.x_label", "axes.y_label", "axes.grid", "axes.grid_alpha", "axes.spine_visible",
        ],
        "axis_limits": True,
    },
    {
        "title": "图例",
        "paths": [
            "legend.show", "legend.loc", "legend.frameon", "legend.fontsize", "custom_text.legend_xy",
        ],
    },
    {
        "title": "线条样式",
        "paths": [
            "line_style.width", "line_style.line_width", "line_style.marker_size",
            "line_style.marker", "line_style.marker_edge_width", "line_style.alpha",
        ],
    },
    {
        "title": "柱状图样式",
        "paths": ["bar_style.width", "bar_style.edge_width", "bar_style.alpha"],
    },
    {
        "title": "散点样式",
        "paths": ["scatter_style.size", "scatter_style.alpha", "scatter_style.edge_width"],
    },
    {
        "title": "热力图样式",
        "paths": ["heatmap.cmap", "heatmap.annot", "heatmap.linewidth", "heatmap.colorbar"],
    },
    {"title": "颜色设置", "glob": "series.*.color"},
    {
        "title": "数据标签",
        "paths": ["data_labels.show", "data_labels.fontsize", "data_labels.offset",
                  "data_labels.decimals", "data_labels.prefix", "data_labels.suffix"],
        "glob_extra": ["series.*.label", "series.*.label_offset"],
    },
    {"title": "自定义文字位置", "paths": ["custom_text.title_xy"]},
    {"title": "导出设置", "paths": ["export.dpi", "export.transparent", "chart.dpi"]},
]


def _group_allowed(group: Dict[str, Any], template_id: Optional[str]) -> bool:
    if not template_id or template_id not in TEMPLATE_GROUP_WHITELIST:
        return True
    return group["title"] in TEMPLATE_GROUP_WHITELIST[template_id]


def _group_has_fields(config: Dict[str, Any], group: Dict[str, Any]) -> bool:
    if group.get("data_import") or group.get("style_presets"):
        return True

    if group.get("font_settings"):
        return path_exists(config, "font")

    if group.get("axis_limits"):
        return path_exists(config, "axes")

    if group.get("canvas_pair"):
        pw, ph = group["canvas_pair"]
        if path_exists(config, pw) and path_exists(config, ph):
            return True
        alt = group.get("canvas_pair_alt")
        if alt and path_exists(config, alt[0]) and path_exists(config, alt[1]):
            return True
        return False

    paths = list(group.get("paths", []))
    if group.get("glob"):
        paths.extend(find_paths(config, glob_pattern=group["glob"]))
    if group.get("glob_extra"):
        for pat in group["glob_extra"]:
            paths.extend(find_paths(config, glob_pattern=pat))

    return any(path_exists(config, p) for p in paths)


def render_simple_panel(
    config: Dict[str, Any],
    prefix: str = "simple",
    template_id: Optional[str] = None,
    project_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """按图表逻辑分组渲染简洁模式控件。"""
    result = config

    for group in SIMPLE_MODE_GROUPS:
        if not _group_allowed(group, template_id):
            continue
        if not _group_has_fields(result, group):
            continue

        expanded_default = group["title"] in (
            "数据导入", "风格预设", "基础信息", "画布尺寸", "字体设置",
        )
        with st.expander(group["title"], expanded=expanded_default):
            if group.get("data_import"):
                result = render_data_panel(
                    result,
                    template_id or "",
                    prefix=f"{prefix}_data",
                    project_root=project_root,
                )
                continue

            if group.get("style_presets"):
                result = render_style_presets(
                    result,
                    prefix=f"{prefix}_style",
                    template_id=template_id or "",
                )
                continue

            if group.get("canvas_pair"):
                pw, ph = group["canvas_pair"]
                if not (path_exists(result, pw) and path_exists(result, ph)):
                    alt = group.get("canvas_pair_alt")
                    if alt:
                        pw, ph = alt
                if path_exists(result, pw) and path_exists(result, ph):
                    result = render_canvas_size(pw, ph, result, prefix=prefix)
                continue

            if group.get("font_settings"):
                font_val = get_by_path(result, "font")
                if isinstance(font_val, dict):
                    updated = render_font_settings(font_val, prefix=prefix)
                    result = set_by_path(result, "font", updated)
                continue

            if group.get("axis_limits") and path_exists(result, "axes"):
                result = render_axis_limit_controls(result, prefix=f"{prefix}_axes")
                paths_axis = [
                    p for p in group.get("paths", []) if path_exists(result, p)
                ]
                for path in paths_axis:
                    value = get_by_path(result, path)
                    new_val = render_field_widget(path, value, prefix=prefix)
                    result = set_by_path(result, path, new_val)
                continue

            paths: List[str] = []
            for p in group.get("paths", []):
                if path_exists(result, p):
                    paths.append(p)
            if group.get("glob"):
                paths.extend(find_paths(result, glob_pattern=group["glob"]))
            if group.get("glob_extra"):
                for pat in group["glob_extra"]:
                    paths.extend(find_paths(result, glob_pattern=pat))

            seen = set()
            for path in paths:
                if path in seen:
                    continue
                seen.add(path)
                value = get_by_path(result, path)
                new_val = render_field_widget(path, value, prefix=prefix)
                result = set_by_path(result, path, new_val)

    return result
