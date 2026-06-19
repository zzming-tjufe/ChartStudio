"""图表标注叠加层 — text / arrow / rectangle。"""

from __future__ import annotations

import warnings
from typing import Any, Dict, List, Optional, Tuple

VALID_COORDS = frozenset({"figure", "axes", "data"})
VALID_TYPES = frozenset({"text", "arrow", "rectangle"})


def _warn(annotation_id: str, reason: str) -> None:
    label = annotation_id or "(无 id)"
    warnings.warn(f"annotation「{label}」已跳过：{reason}", stacklevel=3)


def _resolve_transform(fig, ax, coord: str):
    if coord == "figure":
        return fig.transFigure
    if coord == "axes":
        return ax.transAxes
    return ax.transData


def _parse_coord_point(
    point: Any,
    *,
    annotation_id: str,
    field: str,
) -> Optional[Tuple[str, float, float]]:
    if not isinstance(point, dict):
        _warn(annotation_id, f"{field} 不是对象")
        return None
    coord = str(point.get("coord", "data")).strip().lower()
    if coord not in VALID_COORDS:
        _warn(annotation_id, f"{field}.coord 无效：{coord}")
        return None
    try:
        x = float(point["x"])
        y = float(point["y"])
    except (KeyError, TypeError, ValueError):
        _warn(annotation_id, f"{field} 缺少有效 x/y")
        return None
    return coord, x, y


def _parse_style_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _apply_text(fig, ax, item: dict) -> None:
    ann_id = str(item.get("id", "") or "")
    text = item.get("text")
    if text is None or str(text) == "":
        _warn(ann_id, "text 为空")
        return

    pos = _parse_coord_point(
        item.get("position"),
        annotation_id=ann_id,
        field="position",
    )
    if pos is None:
        return
    coord, x, y = pos
    style = _parse_style_dict(item.get("style"))

    ax.text(
        x,
        y,
        str(text),
        transform=_resolve_transform(fig, ax, coord),
        fontsize=int(style.get("font_size", 10)),
        color=str(style.get("color", "#333333")),
        ha=str(style.get("ha", "center")),
        va=str(style.get("va", "center")),
    )


def _apply_arrow(fig, ax, item: dict) -> None:
    from matplotlib.patches import FancyArrowPatch

    ann_id = str(item.get("id", "") or "")
    start = _parse_coord_point(item.get("start"), annotation_id=ann_id, field="start")
    end = _parse_coord_point(item.get("end"), annotation_id=ann_id, field="end")
    if start is None or end is None:
        return

    start_coord, sx, sy = start
    end_coord, ex, ey = end
    if start_coord != end_coord:
        _warn(ann_id, "start 与 end 的 coord 必须一致")
        return

    style = _parse_style_dict(item.get("style"))
    arrow = FancyArrowPatch(
        (sx, sy),
        (ex, ey),
        transform=_resolve_transform(fig, ax, start_coord),
        arrowstyle=str(style.get("arrowstyle", "->")),
        color=str(style.get("color", "#333333")),
        linewidth=float(style.get("line_width", 1.5)),
        mutation_scale=12,
    )
    ax.add_patch(arrow)


def _apply_rectangle(fig, ax, item: dict) -> None:
    from matplotlib.patches import Rectangle

    ann_id = str(item.get("id", "") or "")
    pos = _parse_coord_point(
        item.get("position"),
        annotation_id=ann_id,
        field="position",
    )
    if pos is None:
        return
    coord, x, y = pos

    size = item.get("size")
    if not isinstance(size, dict):
        _warn(ann_id, "size 不是对象")
        return
    try:
        width = float(size["width"])
        height = float(size["height"])
    except (KeyError, TypeError, ValueError):
        _warn(ann_id, "size 缺少有效 width/height")
        return

    style = _parse_style_dict(item.get("style"))
    rect = Rectangle(
        (x, y),
        width,
        height,
        transform=_resolve_transform(fig, ax, coord),
        facecolor=str(style.get("fill", "none")),
        edgecolor=str(style.get("edge_color", "#333333")),
        linewidth=float(style.get("line_width", 1.0)),
        alpha=float(style.get("alpha", 1.0)),
    )
    ax.add_patch(rect)


def apply_annotations(fig, ax, annotations: list[dict]) -> None:
    """在布局确定后叠加 annotations；单条失败不中断整图。"""
    if not annotations:
        return
    if not isinstance(annotations, list):
        warnings.warn("annotations 不是列表，已忽略", stacklevel=2)
        return

    for item in annotations:
        if not isinstance(item, dict):
            _warn("", "annotation 项不是对象")
            continue
        ann_type = str(item.get("type", "")).strip().lower()
        if ann_type not in VALID_TYPES:
            _warn(str(item.get("id", "") or ""), f"type 无效：{ann_type}")
            continue
        try:
            if ann_type == "text":
                _apply_text(fig, ax, item)
            elif ann_type == "arrow":
                _apply_arrow(fig, ax, item)
            elif ann_type == "rectangle":
                _apply_rectangle(fig, ax, item)
        except Exception as exc:
            _warn(str(item.get("id", "") or ""), f"渲染异常：{type(exc).__name__} — {exc}")
