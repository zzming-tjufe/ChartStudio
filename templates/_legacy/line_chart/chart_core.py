"""
多折线图绘图核心 — 遵循 ChartStudio 标准绘图协议。

所有可调参数从 config 读取，只返回 fig，不调用 plt.show() 或 fig.savefig()。
"""

from __future__ import annotations

from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np


def _hex_to_mpl_color(hex_color: str) -> str:
    """将 #RRGGBB 转为 Matplotlib 可识别的颜色字符串。"""
    if hex_color.startswith("#"):
        return hex_color
    return hex_color


def _get_series_keys(data: Dict[str, Any]) -> List[str]:
    """从 data 中提取除 x 以外的系列键名。"""
    return [k for k in data.keys() if k != "x"]


def draw_chart(config: Dict[str, Any]):
    """
    根据 config 绘制多折线图并返回 Figure 对象。

    Parameters
    ----------
    config : dict
        完整配置，结构与 chart_config.yaml 一致。

    Returns
    -------
    matplotlib.figure.Figure
    """
    chart_cfg = config.get("chart", {})
    font_cfg = config.get("font", {})
    axes_cfg = config.get("axes", {})
    line_cfg = config.get("line_style", {})
    series_cfg = config.get("series", {})
    data = config.get("data", {})

    width = float(chart_cfg.get("width", 10))
    height = float(chart_cfg.get("height", 6))
    dpi = int(chart_cfg.get("dpi", 100))

    fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)

    # 字体设置
    plt.rcParams["font.family"] = font_cfg.get("family", "sans-serif")
    # Windows 下常见中文字体回退
    if "SimHei" not in plt.rcParams.get("font.sans-serif", []):
        plt.rcParams["font.sans-serif"] = [
            font_cfg.get("family", "sans-serif"),
            "SimHei",
            "Microsoft YaHei",
            "DejaVu Sans",
        ]
    plt.rcParams["axes.unicode_minus"] = False

    x_values = data.get("x", [])
    series_keys = _get_series_keys(data)

    for key in series_keys:
        y_values = data.get(key, [])
        s_cfg = series_cfg.get(key, {})
        color = _hex_to_mpl_color(
            s_cfg.get("color", series_cfg.get("overall", {}).get("color", "#1565C0"))
        )
        label = s_cfg.get("label", key)

        ax.plot(
            x_values,
            y_values,
            color=color,
            linewidth=float(line_cfg.get("line_width", 2.0)),
            marker=line_cfg.get("marker", "o"),
            markersize=float(line_cfg.get("marker_size", 6.0)),
            label=label,
        )

    ax.set_title(
        chart_cfg.get("title", ""),
        fontsize=int(font_cfg.get("title_size", 16)),
    )
    ax.set_xlabel(axes_cfg.get("x_label", ""), fontsize=int(font_cfg.get("label_size", 12)))
    ax.set_ylabel(axes_cfg.get("y_label", ""), fontsize=int(font_cfg.get("label_size", 12)))
    ax.tick_params(labelsize=int(font_cfg.get("tick_size", 10)))

    if axes_cfg.get("grid", True):
        ax.grid(True, alpha=float(axes_cfg.get("grid_alpha", 0.3)))

    if series_keys:
        ax.legend()

    fig.tight_layout()
    return fig
