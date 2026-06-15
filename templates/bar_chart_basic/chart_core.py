"""基础柱状图。"""

from __future__ import annotations

from typing import Any, Dict, List

import matplotlib.pyplot as plt

from core.font_runtime import apply_chart_fonts, prepare_chart_fonts


def _bar_colors(config: Dict[str, Any], count: int) -> List[str]:
    """按 series 键顺序解析柱体颜色，优先 series.xxx.color。"""
    series_cfg = config.get("series", {})
    keys = sorted(k for k in series_cfg if k != "overall")
    default = series_cfg.get("overall", {}).get("color", "#1976D2")
    colors: List[str] = []
    for i in range(count):
        if i < len(keys):
            colors.append(series_cfg[keys[i]].get("color", default))
        else:
            colors.append(default)
    return colors


def draw_chart(config: Dict[str, Any]):
    font_bundle = prepare_chart_fonts(config)
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
    colors = _bar_colors(config, len(categories))

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
    ax.set_xticks(list(x_pos))
    ax.set_xticklabels(categories, fontsize=int(font_cfg.get("tick_size", 10)))
    title = chart_cfg.get("title", "")
    if chart_cfg.get("subtitle"):
        title = f"{title}\n{chart_cfg.get('subtitle')}"
    ax.set_title(title, fontsize=int(font_cfg.get("title_size", 16)))
    ax.set_xlabel(axes_cfg.get("x_label", ""), fontsize=int(font_cfg.get("label_size", 12)))
    ax.set_ylabel(axes_cfg.get("y_label", ""), fontsize=int(font_cfg.get("label_size", 12)))

    if axes_cfg.get("grid", True):
        ax.grid(axis="y", alpha=float(axes_cfg.get("grid_alpha", 0.2)))
    if not axes_cfg.get("spine_visible", True):
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)

    if legend_cfg.get("show", False):
        keys = sorted(k for k in series_cfg if k != "overall")
        handles = []
        labels = []
        for i, cat in enumerate(categories):
            if i < len(keys):
                labels.append(series_cfg[keys[i]].get("label", cat))
            else:
                labels.append(cat)
            handles.append(plt.Rectangle((0, 0), 1, 1, fc=colors[i]))
        ax.legend(handles, labels, loc=legend_cfg.get("loc", "best"), frameon=legend_cfg.get("frameon", False))

    if label_cfg.get("show", False):
        for i, v in enumerate(values):
            ax.text(
                i,
                v,
                f"{v:.0f}",
                ha="center",
                va="bottom",
                fontsize=int(label_cfg.get("fontsize", 10)),
            )

    apply_chart_fonts(fig, font_bundle, font_cfg)
    fig.tight_layout()
    return fig
