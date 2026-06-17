"""坐标轴范围控件 — 简洁模式手动 X/Y 范围与 Y 留白。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from core.config_utils import get_by_path, set_by_path


def _pair_from_limit(limit: Any) -> Tuple[Optional[float], Optional[float]]:
    if limit is None:
        return None, None
    if isinstance(limit, (list, tuple)) and len(limit) >= 2:
        try:
            return float(limit[0]), float(limit[1])
        except (TypeError, ValueError):
            return None, None
    return None, None


def render_axis_limit_controls(
    config: Dict[str, Any],
    prefix: str = "axes",
) -> Dict[str, Any]:
    """渲染坐标轴范围控件，写回 axes.xlim / axes.ylim / axes.y_margin。"""
    axes = get_by_path(config, "axes")
    if not isinstance(axes, dict):
        return config

    result = config
    xlo, xhi = _pair_from_limit(axes.get("xlim"))
    ylo, yhi = _pair_from_limit(axes.get("ylim"))
    manual_x = xlo is not None and xhi is not None
    manual_y = ylo is not None and yhi is not None

    manual_x = st.checkbox("手动 X 轴范围", value=manual_x, key=f"{prefix}_manual_x")
    if manual_x:
        c1, c2 = st.columns(2)
        xlo = c1.number_input("X 最小", value=xlo if xlo is not None else 0.0, key=f"{prefix}_xlo")
        xhi = c2.number_input("X 最大", value=xhi if xhi is not None else 1.0, key=f"{prefix}_xhi")
        result = set_by_path(result, "axes.xlim", [float(xlo), float(xhi)])
    else:
        result = set_by_path(result, "axes.xlim", None)

    manual_y = st.checkbox("手动 Y 轴范围", value=manual_y, key=f"{prefix}_manual_y")
    if manual_y:
        c1, c2 = st.columns(2)
        ylo = c1.number_input("Y 最小", value=ylo if ylo is not None else 0.0, key=f"{prefix}_ylo")
        yhi = c2.number_input("Y 最大", value=yhi if yhi is not None else 1.0, key=f"{prefix}_yhi")
        result = set_by_path(result, "axes.ylim", [float(ylo), float(yhi)])
    else:
        result = set_by_path(result, "axes.ylim", None)

    margin = float(axes.get("y_margin", 0.05) or 0.05)
    result = set_by_path(
        result,
        "axes.y_margin",
        st.slider(
            "Y 轴自动留白比例",
            min_value=0.0,
            max_value=0.5,
            value=margin,
            step=0.01,
            key=f"{prefix}_y_margin",
            help="未手动设置 Y 轴范围时，在数据上下方扩展留白。",
        ),
    )
    return result
