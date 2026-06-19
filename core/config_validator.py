"""保存前配置校验。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from core.annotations import VALID_COORDS, VALID_TYPES
from core.chart_linter import run_data_structure_checks
from core.constants import SCHEMA_VERSION
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


    return issues


def _check_protocol_v2(config: dict) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    schema_version = config.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        issues.append(
            ValidationIssue(
                "warn",
                "schema_version",
                f"当前为 {schema_version!r}，保存后将写入 schema_version: {SCHEMA_VERSION}。",
            )
        )

    layout = config.get("layout")
    if isinstance(layout, dict):
        for key in ("left", "right", "bottom", "top"):
            val = layout.get(key)
            if val is None:
                continue
            try:
                fval = float(val)
            except (TypeError, ValueError):
                issues.append(ValidationIssue("error", f"layout.{key}", f"必须是 0~1 之间的数值：{val}"))
                continue
            if not 0.0 <= fval <= 1.0:
                issues.append(ValidationIssue("error", f"layout.{key}", f"必须在 0~1 之间：{fval}"))

        try:
            left = float(layout.get("left", 0))
            right = float(layout.get("right", 1))
            bottom = float(layout.get("bottom", 0))
            top = float(layout.get("top", 1))
            if left >= right:
                issues.append(ValidationIssue("error", "layout", "left 必须小于 right"))
            if bottom >= top:
                issues.append(ValidationIssue("error", "layout", "bottom 必须小于 top"))
        except (TypeError, ValueError):
            pass

    export = config.get("export", {})
    if isinstance(export, dict):
        bbox = str(export.get("bbox", "fixed") or "fixed").strip().lower()
        if bbox not in ("fixed", "tight"):
            issues.append(
                ValidationIssue("error", "export.bbox", f"只能是 fixed 或 tight：{bbox}")
            )

    annotations = config.get("annotations")
    if annotations is not None and not isinstance(annotations, list):
        issues.append(ValidationIssue("error", "annotations", "必须是列表"))
        return issues

    if isinstance(annotations, list):
        seen_ids: set[str] = set()
        for idx, item in enumerate(annotations):
            prefix = f"annotations[{idx}]"
            if not isinstance(item, dict):
                issues.append(ValidationIssue("error", prefix, "annotation 必须是对象"))
                continue

            ann_id = str(item.get("id", "") or "")
            if not ann_id:
                issues.append(ValidationIssue("error", prefix, "缺少 id"))
            elif ann_id in seen_ids:
                issues.append(ValidationIssue("error", f"{prefix}.id", f"重复的 id：{ann_id}"))
            else:
                seen_ids.add(ann_id)

            ann_type = str(item.get("type", "")).strip().lower()
            if ann_type not in VALID_TYPES:
                issues.append(
                    ValidationIssue("error", f"{prefix}.type", f"只能是 text/arrow/rectangle：{ann_type}")
                )

            for point_key in ("position", "start", "end"):
                point = item.get(point_key)
                if point is None:
                    continue
                if not isinstance(point, dict):
                    issues.append(ValidationIssue("error", f"{prefix}.{point_key}", "必须是对象"))
                    continue
                coord = str(point.get("coord", "data")).strip().lower()
                if coord not in VALID_COORDS:
                    issues.append(
                        ValidationIssue("error", f"{prefix}.{point_key}.coord", f"无效 coord：{coord}")
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
    issues.extend(_check_protocol_v2(config))

    data = config.get("data", {})
    if isinstance(data, dict) and not data:
        issues.append(ValidationIssue("warn", "data", "数据段为空，图表可能无法正确展示。"))

    if render_probe is not None:
        try:
            fig = render_probe(config)
            if fig is True:
                pass
            elif fig is None:
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
