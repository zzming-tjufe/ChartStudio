"""基础柱状图。"""

from __future__ import annotations

from typing import Any, Dict, List

import matplotlib.pyplot as plt


from core.annotations import apply_annotations
from core.axis_limits import apply_axis_limits
from core.bar_colors import bar_colors_for_categories
from core.data_label_format import format_data_label
from core.font_utils import apply_legend_fonts, resolve_font_properties
from core.layout import apply_layout
from core.data_keys import category_series_key


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
    legend_cfg = config.get("legend", {})
    series_cfg = config.get("series", {})
    data = config.get("data", {})

    categories = data.get("categories", [])
    values = data.get("values", [])
    colors = _bar_colors(config, categories)

    fig, ax = plt.subplots(
        figsize=(float(fig_cfg.get("width", 9)), float(fig_cfg.get("height", 6))),
        dpi=int(export_cfg.get("dpi", 200)),
    )

    x_pos = range(len(categories))
    ax.bar(
        x_pos,
        values,
        width=float(bar_cfg.get("width", 0.6)),
        color=colors,
        edgecolor="#333333",
        linewidth=float(bar_cfg.get("edge_width", 1.0)),
        alpha=float(bar_cfg.get("alpha", 0.9)),
    )
    title_fp = resolve_font_properties(config, "zh", int(font_cfg.get("title_size", 16)))
    label_fp = resolve_font_properties(config, "zh", int(font_cfg.get("label_size", 12)))
    tick_fp = resolve_font_properties(config, "zh", int(font_cfg.get("tick_size", 10)))
    data_label_fp = resolve_font_properties(config, "zh", int(label_cfg.get("fontsize", 10)))

    ax.set_xticks(list(x_pos))
    ax.set_xticklabels(categories, fontproperties=tick_fp)
    title = chart_cfg.get("title", "")
    if chart_cfg.get("subtitle"):
        title = f"{title}\n{chart_cfg.get('subtitle')}"
    ax.set_title(title, fontproperties=title_fp)
    ax.set_xlabel(axes_cfg.get("x_label", ""), fontproperties=label_fp)
    ax.set_ylabel(axes_cfg.get("y_label", ""), fontproperties=label_fp)
    for label in ax.get_yticklabels():
        label.set_fontproperties(tick_fp)

    if axes_cfg.get("grid", True):
        ax.grid(axis="y", alpha=float(axes_cfg.get("grid_alpha", 0.2)))
    if not axes_cfg.get("spine_visible", True):
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)

    if legend_cfg.get("show", False):
        handles = []
        labels = []
        for i, cat in enumerate(categories):
            key = category_series_key(str(cat))
            entry = series_cfg.get(key, {})
            labels.append(entry.get("label", str(cat)) if isinstance(entry, dict) else str(cat))
            handles.append(plt.Rectangle((0, 0), 1, 1, fc=colors[i]))
        ax.legend(handles, labels, loc=legend_cfg.get("loc", "best"), frameon=legend_cfg.get("frameon", False))
        apply_legend_fonts(ax, config)

    if label_cfg.get("show", False):
        for i, v in enumerate(values):
            ax.text(
                i,
                v,
                format_data_label(v, label_cfg),
                ha="center",
                va="bottom",
                fontproperties=data_label_fp,
            )

    apply_axis_limits(ax, axes_cfg)
    apply_layout(fig, config)
    apply_annotations(fig, ax, config.get("annotations", []), config=config)
    return fig
