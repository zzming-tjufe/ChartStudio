"""
图表质量检查 — 面向论文/报告作者的友好提示。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config_utils import get_by_path, _MISSING
from core.system_fonts import resolve_font_path_by_name


@dataclass
class ChartCheck:
    level: str  # pass | warn | suggest
    title: str
    message: str


def _series_count(data: dict, template_id: str) -> int:
    if not isinstance(data, dict):
        return 0
    if template_id in ("bar_chart_basic", "horizontal_bar_chart"):
        cats = data.get("categories", [])
        return len(cats) if isinstance(cats, list) else 0
    if template_id == "scatter_chart_basic":
        return sum(1 for k, v in data.items() if isinstance(v, dict) and "x" in v)
    if template_id == "heatmap_basic":
        return 0
    return len([k for k in data if k != "x"])


def _has_chinese_font(font_cfg: dict) -> bool:
    if not isinstance(font_cfg, dict):
        return False
    zh_path = str(font_cfg.get("zh_path", "") or "")
    if zh_path and Path(zh_path).is_file():
        return True
    zh_name = str(font_cfg.get("zh_name", "") or "")
    if zh_name and resolve_font_path_by_name(zh_name):
        return True
    file_path = str(font_cfg.get("file_path", "") or "")
    if file_path:
        return True
    return False


def run_data_structure_checks(config: Dict[str, Any], template_id: str = "") -> List[ChartCheck]:
    """检查 data 段内部结构一致性。"""
    checks: List[ChartCheck] = []
    data = config.get("data", {})
    if not isinstance(data, dict) or not data:
        return checks

    if template_id in ("line_chart_basic", "line_chart_report", "line_chart"):
        x = data.get("x", [])
        x_len = len(x) if isinstance(x, list) else 0
        for key, vals in data.items():
            if key == "x":
                continue
            if not isinstance(vals, list):
                checks.append(
                    ChartCheck("warn", "折线数据", f"系列「{key}」不是列表。")
                )
                continue
            if len(vals) != x_len:
                checks.append(
                    ChartCheck(
                        "warn",
                        "折线数据",
                        f"系列「{key}」长度 {len(vals)} 与 X 轴 {x_len} 不一致。",
                    )
                )

    elif template_id in ("bar_chart_basic", "horizontal_bar_chart"):
        cats = data.get("categories", [])
        vals = data.get("values", [])
        if isinstance(cats, list) and isinstance(vals, list) and len(cats) != len(vals):
            checks.append(
                ChartCheck(
                    "warn",
                    "柱状数据",
                    f"categories（{len(cats)}）与 values（{len(vals)}）长度不一致。",
                )
            )

    elif template_id == "scatter_chart_basic":
        for key, grp in data.items():
            if not isinstance(grp, dict):
                continue
            xs, ys = grp.get("x", []), grp.get("y", [])
            if isinstance(xs, list) and isinstance(ys, list) and len(xs) != len(ys):
                checks.append(
                    ChartCheck(
                        "warn",
                        "散点数据",
                        f"分组「{key}」X（{len(xs)}）与 Y（{len(ys)}）长度不一致。",
                    )
                )

    elif template_id == "heatmap_basic":
        matrix = data.get("matrix", [])
        xl = data.get("x_labels", [])
        yl = data.get("y_labels", [])
        if isinstance(matrix, list) and matrix:
            nrows = len(matrix)
            ncols = len(matrix[0]) if matrix[0] else 0
            if isinstance(yl, list) and len(yl) != nrows:
                checks.append(
                    ChartCheck(
                        "warn",
                        "热力图数据",
                        f"matrix 行数 {nrows} 与 y_labels（{len(yl)}）不一致。",
                    )
                )
            if isinstance(xl, list) and len(xl) != ncols:
                checks.append(
                    ChartCheck(
                        "warn",
                        "热力图数据",
                        f"matrix 列数 {ncols} 与 x_labels（{len(xl)}）不一致。",
                    )
                )

    return checks


def run_chart_checks(config: Dict[str, Any], template_id: str = "") -> List[ChartCheck]:
    checks: List[ChartCheck] = []
    chart = config.get("chart", {}) if isinstance(config.get("chart"), dict) else {}
    axes = config.get("axes", {}) if isinstance(config.get("axes"), dict) else {}
    legend = config.get("legend", {}) if isinstance(config.get("legend"), dict) else {}
    font = config.get("font", {}) if isinstance(config.get("font"), dict) else {}
    export = config.get("export", {}) if isinstance(config.get("export"), dict) else {}
    figure = config.get("figure", config.get("chart", {}))
    data = config.get("data", {}) if isinstance(config.get("data"), dict) else {}

    dpi = export.get("dpi", config.get("chart", {}).get("dpi", 150))
    try:
        dpi_int = int(dpi)
    except (TypeError, ValueError):
        dpi_int = 150

    if _has_chinese_font(font):
        checks.append(ChartCheck("pass", "中文字体", "已配置可用的中文字体。"))
    else:
        checks.append(
            ChartCheck(
                "warn",
                "中文字体",
                "未检测到中文字体路径或系统字体，中文可能显示为方框。请在「字体设置」中选择字体。",
            )
        )

    if dpi_int >= 300:
        checks.append(ChartCheck("pass", "导出 DPI", f"当前 {dpi_int}，适合论文印刷。"))
    elif dpi_int >= 200:
        checks.append(
            ChartCheck(
                "suggest",
                "导出 DPI",
                f"当前 {dpi_int}，屏幕展示足够；论文投稿建议设为 300。",
            )
        )
    else:
        checks.append(
            ChartCheck(
                "warn",
                "导出 DPI",
                f"当前 {dpi_int} 偏低，导出可能不够清晰，建议至少 200–300。",
            )
        )

    title = str(chart.get("title", "") or "").strip()
    if title:
        checks.append(ChartCheck("pass", "图表标题", f"已设置：「{title[:20]}」"))
    else:
        checks.append(ChartCheck("warn", "图表标题", "标题为空，论文图通常需要简短标题。"))

    x_label = str(axes.get("x_label", "") or "").strip()
    y_label = str(axes.get("y_label", "") or "").strip()
    if x_label and y_label:
        checks.append(ChartCheck("pass", "坐标轴标题", "X/Y 轴标题均已填写。"))
    elif x_label or y_label:
        checks.append(ChartCheck("suggest", "坐标轴标题", "建议同时填写 X 轴与 Y 轴标题。"))
    else:
        checks.append(ChartCheck("warn", "坐标轴标题", "坐标轴标题均为空，读者可能不清楚变量含义。"))

    legend_show = bool(legend.get("show", False))
    n_series = _series_count(data, template_id)
    if legend_show and n_series <= 1:
        checks.append(
            ChartCheck(
                "suggest",
                "图例",
                "图例已开启，但数据似乎只有单系列，可考虑关闭图例以简化版面。",
            )
        )
    elif legend_show and n_series > 1:
        checks.append(ChartCheck("pass", "图例", f"多系列数据（{n_series} 组），图例已开启。"))
    else:
        checks.append(ChartCheck("pass", "图例", "当前图例设置与数据匹配。"))

    long_labels = False
    if template_id in ("bar_chart_basic", "horizontal_bar_chart"):
        cats = data.get("categories", [])
        if isinstance(cats, list):
            long_labels = any(len(str(c)) > 8 for c in cats)
    elif template_id == "heatmap_basic":
        xl = data.get("x_labels", [])
        if isinstance(xl, list):
            long_labels = any(len(str(c)) > 10 for c in xl)
    if long_labels:
        checks.append(
            ChartCheck(
                "suggest",
                "轴标签长度",
                "部分类别标签较长，可考虑缩短文字或改用横向柱状图。",
            )
        )
    else:
        checks.append(ChartCheck("pass", "轴标签", "轴标签长度适中。"))

    try:
        w = float(figure.get("width", 10))
        h = float(figure.get("height", 6))
        ratio = w / h if h > 0 else 1
        if ratio > 2.5:
            checks.append(
                ChartCheck(
                    "suggest",
                    "画布比例",
                    f"当前宽高比 {ratio:.1f}:1 偏宽，嵌入双栏论文时可适当减小宽度。",
                )
            )
        elif ratio < 0.6:
            checks.append(
                ChartCheck(
                    "suggest",
                    "画布比例",
                    f"当前宽高比 {ratio:.1f}:1 偏高，可考虑加宽画布。",
                )
            )
        else:
            checks.append(ChartCheck("pass", "画布比例", f"宽高比 {ratio:.1f}:1 较合理。"))
    except (TypeError, ValueError):
        checks.append(ChartCheck("pass", "画布比例", "无法解析画布尺寸。"))

    transparent = bool(export.get("transparent", False))
    if transparent:
        checks.append(
            ChartCheck(
                "suggest",
                "透明背景",
                "已开启透明背景，适合 PPT；论文 Word 排版通常建议关闭。",
            )
        )
    else:
        checks.append(ChartCheck("pass", "透明背景", "使用实心背景，适合打印与 Word 嵌入。"))

    checks.extend(run_data_structure_checks(config, template_id))

    return checks


def render_chart_checks_panel(config: Dict[str, Any], template_id: str = "") -> None:
    import streamlit as st

    checks = run_chart_checks(config, template_id)
    level_icon = {"pass": "✅", "warn": "⚠️", "suggest": "💡"}
    level_label = {"pass": "通过", "warn": "提醒", "suggest": "建议"}
    for c in checks:
        icon = level_icon.get(c.level, "·")
        label = level_label.get(c.level, c.level)
        st.markdown(f"{icon} **{c.title}**（{label}）— {c.message}")
