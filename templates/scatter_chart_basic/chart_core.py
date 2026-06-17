"""基础散点图 — 支持多组数据。"""

from __future__ import annotations

from typing import Any, Dict, List

import matplotlib.pyplot as plt

from core.axis_limits import apply_axis_limits


def _group_keys(data: Dict[str, Any]) -> List[str]:
    return [k for k in data if isinstance(data.get(k), dict)]


def draw_chart(config: Dict[str, Any]):
    chart_cfg = config.get("chart", {})
    fig_cfg = config.get("figure", {})
    export_cfg = config.get("export", {})
    font_cfg = config.get("font", {})
    axes_cfg = config.get("axes", {})
    legend_cfg = config.get("legend", {})
    scatter_cfg = config.get("scatter_style", {})
    series_cfg = config.get("series", {})
    custom_cfg = config.get("custom_text", {})
    data = config.get("data", {})

    fig, ax = plt.subplots(
        figsize=(float(fig_cfg.get("width", 8)), float(fig_cfg.get("height", 7))),
        dpi=int(export_cfg.get("dpi", 200)),
    )

    for key in _group_keys(data):
        grp = data[key]
        s_cfg = series_cfg.get(key, {})
        ax.scatter(
            grp.get("x", []),
            grp.get("y", []),
            s=float(scatter_cfg.get("size", 60)),
            c=s_cfg.get("color", series_cfg.get("overall", {}).get("color", "#5E35B1")),
            alpha=float(scatter_cfg.get("alpha", 0.75)),
            edgecolors="#333333",
            linewidths=float(scatter_cfg.get("edge_width", 0.8)),
            label=s_cfg.get("label", key),
        )

    title = chart_cfg.get("title", "")
    if chart_cfg.get("subtitle"):
        title = f"{title}\n{chart_cfg.get('subtitle')}"
    title_obj = ax.set_title(title, fontsize=int(font_cfg.get("title_size", 16)))
    title_xy = custom_cfg.get("title_xy")
    if isinstance(title_xy, list) and len(title_xy) >= 2:
        title_obj.set_position((float(title_xy[0]), float(title_xy[1])))

    ax.set_xlabel(axes_cfg.get("x_label", ""), fontsize=int(font_cfg.get("label_size", 12)))
    ax.set_ylabel(axes_cfg.get("y_label", ""), fontsize=int(font_cfg.get("label_size", 12)))
    ax.tick_params(labelsize=int(font_cfg.get("tick_size", 10)))

    if axes_cfg.get("grid", True):
        ax.grid(True, alpha=float(axes_cfg.get("grid_alpha", 0.25)))
    if not axes_cfg.get("spine_visible", True):
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)

    if legend_cfg.get("show", True) and _group_keys(data):
        leg_xy = custom_cfg.get("legend_xy")
        legend_kwargs = {
            "loc": legend_cfg.get("loc", "best"),
            "frameon": legend_cfg.get("frameon", True),
            "fontsize": int(font_cfg.get("legend_size", 10)),
        }
        if isinstance(leg_xy, list) and len(leg_xy) >= 2:
            legend_kwargs["bbox_to_anchor"] = (float(leg_xy[0]), float(leg_xy[1]))
        ax.legend(**legend_kwargs)

    apply_axis_limits(ax, axes_cfg)
    fig.tight_layout()
    return fig
