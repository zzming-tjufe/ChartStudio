"""保存前配置校验。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from core.chart_linter import run_data_structure_checks
from core.field_options import SELECT_FIELD_OPTIONS
from core.heatmap_cmaps import is_valid_cmap

_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


@dataclass
class ValidationIssue:
    level: str  # error | warn
    field: str
    message: str


def _check_colors(config: dict) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    series = config.get("series", {})
    if isinstance(series, dict):
        for key, entry in series.items():
            if not isinstance(entry, dict):
                continue
            color = entry.get("color")
            if color and not _COLOR_RE.match(str(color)):
                issues.append(
                    ValidationIssue("error", f"series.{key}.color", f"颜色格式无效：{color}")
                )
    return issues


def _check_select_fields(config: dict) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    legend = config.get("legend", {})
    if isinstance(legend, dict):
        loc = legend.get("loc")
        allowed = SELECT_FIELD_OPTIONS.get("legend.loc", [])
        if loc and allowed and str(loc) not in allowed:
            issues.append(ValidationIssue("error", "legend.loc", f"图例位置无效：{loc}"))

    line_style = config.get("line_style", {})
    if isinstance(line_style, dict):
        marker = line_style.get("marker")
        allowed = SELECT_FIELD_OPTIONS.get("line_style.marker", [])
        if marker is not None and allowed and str(marker) not in allowed:
            issues.append(ValidationIssue("error", "line_style.marker", f"标记形状无效：{marker}"))

    heatmap = config.get("heatmap", {})
    if isinstance(heatmap, dict):
        cmap = heatmap.get("cmap")
        if cmap and not is_valid_cmap(str(cmap)):
            issues.append(
                ValidationIssue(
                    "warn",
                    "heatmap.cmap",
                    f"色图「{cmap}」不在推荐列表中，建议在面板中重新选择。",
                )
            )

    return issues


def validate_config_for_save(
    config: dict,
    template_id: str = "",
    *,
    render_probe: Optional[Callable[[dict], Any]] = None,
) -> List[ValidationIssue]:
    """保存前校验，返回 error / warn 列表。"""
    issues: List[ValidationIssue] = []

    for check in run_data_structure_checks(config, template_id):
        if check.level in ("warn", "error"):
            issues.append(ValidationIssue("error", check.title, check.message))

    issues.extend(_check_colors(config))
    issues.extend(_check_select_fields(config))

    data = config.get("data", {})
    if isinstance(data, dict) and not data:
        issues.append(ValidationIssue("warn", "data", "数据段为空，图表可能无法正确展示。"))

    if render_probe is not None:
        try:
            fig = render_probe(config)
            if fig is None:
                issues.append(
                    ValidationIssue("error", "render", "绘图函数未返回有效图表对象。")
                )
            else:
                try:
                    import matplotlib.pyplot as plt

                    plt.close(fig)
                except Exception:
                    pass
        except Exception as exc:
            issues.append(
                ValidationIssue("error", "render", f"渲染探测失败：{type(exc).__name__} — {exc}")
            )

    return issues


def has_blocking_errors(issues: List[ValidationIssue]) -> bool:
    return any(i.level == "error" for i in issues)
