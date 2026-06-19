"""坐标轴范围 — 从 config.axes 解析并应用到 matplotlib Axes。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _is_auto(limit: Any) -> bool:
    if limit is None:
        return True
    if isinstance(limit, str) and limit.lower() in ("auto", "none", ""):
        return True
    return False


def _parse_pair(limit: Any) -> Optional[Tuple[float, float]]:
    if _is_auto(limit):
        return None
    if isinstance(limit, (list, tuple)) and len(limit) >= 2:
        try:
            return float(limit[0]), float(limit[1])
        except (TypeError, ValueError):
            return None
    return None


def apply_axis_limits(ax, axes_cfg: Dict[str, Any]) -> None:
    """应用 xlim / ylim；y_margin 在自动模式下扩展 Y 轴留白。"""
    if not isinstance(axes_cfg, dict):
        return

    xlim = _parse_pair(axes_cfg.get("xlim"))
    ylim = _parse_pair(axes_cfg.get("ylim"))

    if xlim:
        ax.set_xlim(xlim)
    if ylim:
        ax.set_ylim(ylim)

    if not ylim:
        margin = axes_cfg.get("y_margin")
        try:
            margin_f = float(margin) if margin is not None else None
        except (TypeError, ValueError):
            margin_f = None
        if margin_f is not None and margin_f > 0:
            ymin, ymax = ax.get_ylim()
            span = ymax - ymin if ymax > ymin else 1.0
            pad = span * margin_f
            ax.set_ylim(ymin - pad, ymax + pad)
