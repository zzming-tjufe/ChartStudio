"""图表布局 — 从 config.layout 应用 subplots_adjust 或 tight_layout。"""

from __future__ import annotations

from typing import Any, Dict

DEFAULT_LAYOUT: Dict[str, Any] = {
    "left": 0.12,
    "right": 0.95,
    "bottom": 0.16,
    "top": 0.88,
    "use_tight_layout": False,
}


def _float_val(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def apply_layout(fig, config: dict) -> None:
    """读取 config.layout 并应用到 figure。"""
    layout = config.get("layout")
    if not isinstance(layout, dict):
        layout = {}

    if bool(layout.get("use_tight_layout", DEFAULT_LAYOUT["use_tight_layout"])):
        fig.tight_layout()
        return

    fig.subplots_adjust(
        left=_float_val(layout.get("left"), DEFAULT_LAYOUT["left"]),
        right=_float_val(layout.get("right"), DEFAULT_LAYOUT["right"]),
        bottom=_float_val(layout.get("bottom"), DEFAULT_LAYOUT["bottom"]),
        top=_float_val(layout.get("top"), DEFAULT_LAYOUT["top"]),
    )
