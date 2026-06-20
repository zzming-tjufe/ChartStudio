"""
风格预设 — 批量应用样式配置（不修改 data）。
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

import streamlit as st

from core.data_keys import category_series_key
from core.session_utils import clear_config_widget_state

STYLE_ROOT_KEYS = frozenset(
    {
        "chart",
        "figure",
        "export",
        "font",
        "axes",
        "legend",
        "line_style",
        "bar_style",
        "scatter_style",
        "heatmap",
        "series",
        "custom_text",
        "data_labels",
    }
)

# _palette 为内部字段，会按当前 data 写入各系列/柱条颜色
PRESET_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "学术论文风": {
        "_palette": ["#2C3E50", "#7F8C8D", "#16A085", "#8E44AD"],
        "figure": {"width": 8.0, "height": 5.0},
        "export": {"dpi": 300, "transparent": False},
        "font": {
            "zh_name": "SimSun",
            "en_name": "Times New Roman",
            "num_name": "Times New Roman",
            "title_size": 14,
            "label_size": 12,
            "tick_size": 10,
            "legend_size": 10,
        },
        "axes": {"grid": True, "grid_alpha": 0.2, "spine_visible": True},
        "legend": {"frameon": True, "loc": "upper right"},
        "line_style": {"width": 1.5, "marker": "s", "marker_size": 5.0, "alpha": 1.0},
        "bar_style": {"width": 0.55, "alpha": 0.85},
        "scatter_style": {"size": 55.0, "alpha": 0.85},
        "heatmap": {"cmap": "RdBu_r", "annot": True},
    },
    "中文报告风": {
        "_palette": ["#D32F2F", "#1976D2", "#388E3C", "#F57C00"],
        "figure": {"width": 10.0, "height": 6.0},
        "export": {"dpi": 200, "transparent": False},
        "font": {
            "zh_name": "Microsoft YaHei",
            "en_name": "Arial",
            "num_name": "Arial",
            "title_size": 20,
            "label_size": 14,
            "tick_size": 12,
            "legend_size": 12,
        },
        "axes": {"grid": True, "grid_alpha": 0.35, "spine_visible": True},
        "legend": {"frameon": True, "loc": "best"},
        "line_style": {"width": 2.5, "marker": "o", "marker_size": 7.0},
        "bar_style": {"width": 0.65, "alpha": 0.92},
        "scatter_style": {"size": 80.0, "alpha": 0.9},
        "heatmap": {"cmap": "YlOrRd", "annot": True},
    },
    "蓝色科技风": {
        "_palette": ["#0D47A1", "#1565C0", "#42A5F5", "#90CAF9"],
        "figure": {"width": 11.0, "height": 6.0},
        "export": {"dpi": 200, "transparent": False},
        "font": {
            "zh_name": "Microsoft YaHei",
            "en_name": "Arial",
            "num_name": "Arial",
            "title_size": 16,
            "label_size": 12,
            "tick_size": 10,
            "legend_size": 10,
        },
        "axes": {"grid": True, "grid_alpha": 0.12, "spine_visible": False},
        "legend": {"frameon": False, "loc": "upper right"},
        "line_style": {"width": 2.8, "marker": "D", "marker_size": 6.5, "alpha": 0.95},
        "bar_style": {"width": 0.6, "alpha": 0.9, "edge_width": 0.5},
        "scatter_style": {"size": 70.0, "alpha": 0.88},
        "heatmap": {"cmap": "Blues", "annot": True},
    },
    "黑白打印风": {
        "_palette": ["#111111", "#444444", "#777777", "#AAAAAA"],
        "figure": {"width": 8.5, "height": 5.5},
        "export": {"dpi": 300, "transparent": False},
        "font": {
            "zh_name": "SimHei",
            "en_name": "Times New Roman",
            "num_name": "Times New Roman",
            "title_size": 14,
            "label_size": 12,
            "tick_size": 10,
            "legend_size": 10,
        },
        "axes": {"grid": True, "grid_alpha": 0.12, "spine_visible": True},
        "legend": {"frameon": True, "loc": "best"},
        "line_style": {"width": 1.8, "marker": "^", "marker_size": 5.5, "alpha": 1.0},
        "bar_style": {"width": 0.55, "edge_width": 1.4, "alpha": 0.95},
        "scatter_style": {"size": 60.0, "alpha": 1.0, "edge_width": 1.2},
        "heatmap": {"cmap": "Greys", "annot": True},
    },
    "答辩 PPT 风": {
        "_palette": ["#1565C0", "#E91E63", "#FFC107", "#00BCD4"],
        "export": {"dpi": 150, "transparent": True},
        "figure": {"width": 12.0, "height": 6.5},
        "font": {
            "zh_name": "Microsoft YaHei",
            "en_name": "Arial",
            "num_name": "Arial",
            "title_size": 24,
            "label_size": 18,
            "tick_size": 15,
            "legend_size": 15,
        },
        "axes": {"grid": False, "spine_visible": False},
        "legend": {"frameon": False, "loc": "upper left"},
        "line_style": {"width": 3.5, "marker": "o", "marker_size": 10.0},
        "bar_style": {"width": 0.7, "alpha": 0.95, "edge_width": 0.0},
        "scatter_style": {"size": 120.0, "alpha": 0.92},
        "heatmap": {"cmap": "plasma", "annot": True},
        "data_labels": {"show": True, "fontsize": 11},
    },
}

PRESET_HINTS: Dict[str, str] = {
    "学术论文风": "紧凑画布 · 低饱和配色 · 方点标记",
    "中文报告风": "大字号 · 高对比配色 · 粗线条",
    "蓝色科技风": "无边框 · 蓝色系 · 菱形标记",
    "黑白打印风": "灰度配色 · 适合打印",
    "答辩 PPT 风": "透明背景 · 超大字号 · 鲜艳配色",
}


def _deep_merge(base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    result = deepcopy(base)
    for key, val in patch.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = deepcopy(val)
    return result


def _style_target_keys(data: Dict[str, Any], template_id: str) -> List[str]:
    """根据 data 结构列出应着色的 series 键。"""
    if not isinstance(data, dict):
        return []

    if template_id in ("line_chart_basic", "line_chart_report", "line_chart"):
        return [k for k in data if k != "x" and isinstance(data.get(k), list)]

    if template_id in ("bar_chart_basic", "horizontal_bar_chart"):
        cats = data.get("categories", [])
        if isinstance(cats, list):
            return [category_series_key(str(c)) for c in cats]
        return []

    if template_id == "scatter_chart_basic":
        return [
            k
            for k, v in data.items()
            if isinstance(v, dict) and "x" in v and "y" in v
        ]

    return []


def _apply_palette(
    config: Dict[str, Any],
    palette: List[str],
    template_id: str,
) -> None:
    """将调色板写入当前数据对应的全部系列/柱条颜色。"""
    if not palette:
        return

    data = config.get("data", {})
    keys = _style_target_keys(data, template_id)
    series = config.setdefault("series", {})
    if not isinstance(series, dict):
        series = {}
        config["series"] = series

    for i, key in enumerate(keys):
        color = palette[i % len(palette)]
        entry = series.get(key)
        if isinstance(entry, dict):
            entry["color"] = color
        else:
            series[key] = {"color": color}

    overall = series.setdefault("overall", {})
    if isinstance(overall, dict):
        overall["color"] = palette[0]


def apply_style_preset(
    config: Dict[str, Any],
    preset_name: str,
    *,
    template_id: str = "",
) -> Dict[str, Any]:
    """应用风格预设，仅覆盖样式相关键，保留 data。"""
    raw_patch = PRESET_DEFINITIONS.get(preset_name)
    if not raw_patch:
        return config

    patch = deepcopy(raw_patch)
    palette = patch.pop("_palette", None)

    result = deepcopy(config)
    data_backup = result.get("data")

    for key, val in patch.items():
        if key not in STYLE_ROOT_KEYS:
            continue
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = deepcopy(val)

    if isinstance(palette, list) and palette:
        _apply_palette(result, palette, template_id)

    if data_backup is not None:
        result["data"] = data_backup
    return result


def list_presets() -> List[str]:
    return list(PRESET_DEFINITIONS.keys())


def render_style_presets(
    config: Dict[str, Any],
    prefix: str = "style",
    *,
    template_id: str = "",
) -> Dict[str, Any]:
    """简洁模式「风格预设」分组 UI。"""
    st.caption("一键套用常见论文/报告/PPT 风格，会同步更新配色、线宽、字号等（不修改数据）。")
    presets = list_presets()
    cols = st.columns(min(len(presets), 3))
    for i, name in enumerate(presets):
        with cols[i % len(cols)]:
            if st.button(name, key=f"{prefix}_preset_{i}", use_container_width=True):
                applied = apply_style_preset(config, name, template_id=template_id)
                st.session_state.current_config = applied
                st.session_state[f"{prefix}_applied"] = name
                clear_config_widget_state()
                st.rerun()

    applied = st.session_state.get(f"{prefix}_applied")
    if applied:
        hint = PRESET_HINTS.get(applied, "")
        st.success(f"已应用预设：{applied}" + (f"（{hint}）" if hint else ""))

    with st.expander("各预设特点", expanded=False):
        for name in presets:
            st.markdown(f"- **{name}**：{PRESET_HINTS.get(name, '')}")

    return config
