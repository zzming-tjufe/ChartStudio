"""报告风格多折线图 — 适合论文/报告排版。"""

from __future__ import annotations

from typing import Any, Dict, List

import matplotlib.pyplot as plt

from core.axis_limits import apply_axis_limits
from core.data_label_format import format_data_label


def _series_keys(data: Dict[str, Any]) -> List[str]:
    return [k for k in data if k != "x"]


def _apply_data_labels(ax, config: Dict[str, Any], series_cfg: Dict[str, Any]) -> None:
    label_cfg = config.get("data_labels", {})
    if not label_cfg.get("show", False):
        return
    fontsize = int(label_cfg.get("fontsize", 9))
    for line in ax.get_lines():
        label = line.get_label()
        key = next((k for k in _series_keys(config.get("data", {})) if series_cfg.get(k, {}).get("label", k) == label), None)
        offset = series_cfg.get(key, {}).get("label_offset", [0, 4]) if key else [0, 4]
        dx, dy = (float(offset[0]), float(offset[1])) if isinstance(offset, list) and len(offset) >= 2 else (0.0, 4.0)
        for x, y in zip(line.get_xdata(), line.get_ydata()):
            ax.annotate(
                format_data_label(y, label_cfg),
                (x, y),
                textcoords="offset points",
                xytext=(dx * 10, dy * 10),
                ha="center",
                fontsize=fontsize,
            )


def draw_chart(config: Dict[str, Any]):
    chart_cfg = config.get("chart", {})
    fig_cfg = config.get("figure", {})
    export_cfg = config.get("export", {})
    font_cfg = config.get("font", {})
    axes_cfg = config.get("axes", {})
    legend_cfg = config.get("legend", {})
    line_cfg = config.get("line_style", {})
    series_cfg = config.get("series", {})
    custom_cfg = config.get("custom_text", {})
    data = config.get("data", {})

    fig, ax = plt.subplots(
        figsize=(float(fig_cfg.get("width", 12)), float(fig_cfg.get("height", 7))),
        dpi=int(export_cfg.get("dpi", 300)),
    )

    x_values = data.get("x", [])
    for key in _series_keys(data):
        s_cfg = series_cfg.get(key, {})
        ax.plot(
            x_values,
            data.get(key, []),
            color=s_cfg.get("color", series_cfg.get("overall", {}).get("color", "#1565C0")),
            linewidth=float(line_cfg.get("width", 2.5)),
            marker=line_cfg.get("marker", "s"),
            markersize=float(line_cfg.get("marker_size", 7.0)),
            markeredgewidth=float(line_cfg.get("marker_edge_width", 1.2)),
            alpha=float(line_cfg.get("alpha", 0.95)),
            label=s_cfg.get("label", key),
        )

    title = chart_cfg.get("title", "")
    subtitle = chart_cfg.get("subtitle", "")
    if subtitle:
        title = f"{title}\n{subtitle}"
    title_obj = ax.set_title(title, fontsize=int(font_cfg.get("title_size", 18)), pad=14)
    title_xy = custom_cfg.get("title_xy")
    if isinstance(title_xy, list) and len(title_xy) >= 2:
        title_obj.set_position((float(title_xy[0]), float(title_xy[1])))

    ax.set_xlabel(axes_cfg.get("x_label", ""), fontsize=int(font_cfg.get("label_size", 13)))
    ax.set_ylabel(axes_cfg.get("y_label", ""), fontsize=int(font_cfg.get("label_size", 13)))
    ax.tick_params(labelsize=int(font_cfg.get("tick_size", 11)))

    if axes_cfg.get("grid", True):
        ax.grid(True, alpha=float(axes_cfg.get("grid_alpha", 0.25)), linestyle="--")
    if not axes_cfg.get("spine_visible", False):
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)

    if legend_cfg.get("show", True) and _series_keys(data):
        leg_xy = custom_cfg.get("legend_xy", [0.02, 0.98])
        ax.legend(
            loc=legend_cfg.get("loc", "upper left"),
            frameon=legend_cfg.get("frameon", True),
            fontsize=int(legend_cfg.get("fontsize", font_cfg.get("legend_size", 11))),
            bbox_to_anchor=(float(leg_xy[0]), float(leg_xy[1])) if isinstance(leg_xy, list) else None,
        )

    _apply_data_labels(ax, config, series_cfg)
    apply_axis_limits(ax, axes_cfg)
    fig.tight_layout()
    return fig
