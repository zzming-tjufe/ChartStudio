"""基础热力图。"""

from __future__ import annotations

from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np

from core.axis_limits import apply_axis_limits
from core.data_label_format import format_data_label


def draw_chart(config: Dict[str, Any]):
    chart_cfg = config.get("chart", {})
    fig_cfg = config.get("figure", {})
    export_cfg = config.get("export", {})
    font_cfg = config.get("font", {})
    axes_cfg = config.get("axes", {})
    heat_cfg = config.get("heatmap", {})
    label_cfg = config.get("data_labels", {})
    data = config.get("data", {})

    matrix = np.array(data.get("matrix", [[0]]), dtype=float)
    x_labels = data.get("x_labels", [])
    y_labels = data.get("y_labels", [])
    nrows, ncols = matrix.shape
    linewidth = float(heat_cfg.get("linewidth", 0.5))

    fig, ax = plt.subplots(
        figsize=(float(fig_cfg.get("width", 8)), float(fig_cfg.get("height", 7))),
        dpi=int(export_cfg.get("dpi", 200)),
    )

    im = ax.imshow(matrix, cmap=heat_cfg.get("cmap", "RdYlBu_r"), aspect="auto")

    if x_labels:
        ax.set_xticks(range(len(x_labels)))
        ax.set_xticklabels(x_labels, fontsize=int(font_cfg.get("tick_size", 9)), rotation=45, ha="right")
    if y_labels:
        ax.set_yticks(range(len(y_labels)))
        ax.set_yticklabels(y_labels, fontsize=int(font_cfg.get("tick_size", 9)))

    if linewidth > 0:
        ax.set_xticks(np.arange(-0.5, ncols, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, nrows, 1), minor=True)
        ax.grid(which="minor", color="white", linestyle="-", linewidth=linewidth)
        ax.tick_params(which="minor", bottom=False, left=False)

    if heat_cfg.get("annot", True):
        for i in range(nrows):
            for j in range(ncols):
                ax.text(
                    j,
                    i,
                    format_data_label(matrix[i, j], label_cfg),
                    ha="center",
                    va="center",
                    color="black",
                    fontsize=int(font_cfg.get("tick_size", 9)),
                )

    title = chart_cfg.get("title", "")
    if chart_cfg.get("subtitle"):
        title = f"{title}\n{chart_cfg.get('subtitle')}"
    ax.set_title(title, fontsize=int(font_cfg.get("title_size", 16)))
    ax.set_xlabel(axes_cfg.get("x_label", ""), fontsize=int(font_cfg.get("label_size", 12)))
    ax.set_ylabel(axes_cfg.get("y_label", ""), fontsize=int(font_cfg.get("label_size", 12)))

    if axes_cfg.get("grid", False):
        ax.grid(which="major", alpha=float(axes_cfg.get("grid_alpha", 0.3)))

    if heat_cfg.get("colorbar", True):
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    apply_axis_limits(ax, axes_cfg)
    fig.tight_layout()
    return fig
