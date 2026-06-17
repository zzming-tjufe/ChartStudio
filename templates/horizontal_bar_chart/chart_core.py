"""横向柱状图。"""

from __future__ import annotations

from typing import Any, Dict, List

import matplotlib.pyplot as plt


from core.axis_limits import apply_axis_limits
from core.bar_colors import bar_colors_for_categories
from core.data_label_format import format_data_label


def _bar_colors(config: Dict[str, Any], categories: List[str]) -> List[str]:
    return bar_colors_for_categories(config, categories)


def draw_chart(config: Dict[str, Any]):
    chart_cfg = config.get("chart", {})
    fig_cfg = config.get("figure", {})
    export_cfg = config.get("export", {})
    font_cfg = config.get("font", {})
    axes_cfg = config.get("axes", {})
    bar_cfg = config.get("bar_style", {})
    label_cfg = config.get("data_labels", {})
    data = config.get("data", {})

    categories = data.get("categories", [])
    values = data.get("values", [])
    colors = _bar_colors(config, categories)

    fig, ax = plt.subplots(
        figsize=(float(fig_cfg.get("width", 10)), float(fig_cfg.get("height", 6))),
        dpi=int(export_cfg.get("dpi", 200)),
    )

    y_pos = range(len(categories))
    ax.barh(
        y_pos,
        values,
        height=float(bar_cfg.get("width", 0.65)),
        color=colors,
        edgecolor="#444444",
        linewidth=float(bar_cfg.get("edge_width", 0.8)),
        alpha=float(bar_cfg.get("alpha", 0.88)),
    )
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(categories, fontsize=int(font_cfg.get("tick_size", 10)))
    ax.set_title(chart_cfg.get("title", ""), fontsize=int(font_cfg.get("title_size", 16)))
    ax.set_xlabel(axes_cfg.get("x_label", ""), fontsize=int(font_cfg.get("label_size", 12)))
    ax.set_ylabel(axes_cfg.get("y_label", ""), fontsize=int(font_cfg.get("label_size", 12)))

    if axes_cfg.get("grid", True):
        ax.grid(axis="x", alpha=float(axes_cfg.get("grid_alpha", 0.2)))

    if label_cfg.get("show", False):
        for i, v in enumerate(values):
            ax.text(
                v,
                i,
                format_data_label(v, label_cfg),
                va="center",
                fontsize=int(label_cfg.get("fontsize", 9)),
            )

    apply_axis_limits(ax, axes_cfg)
    fig.tight_layout()
    return fig
