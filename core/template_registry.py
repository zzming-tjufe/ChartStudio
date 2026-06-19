"""Central template metadata for ChartStudio.

Keeping template capabilities in one place makes it much cheaper to add new
chart types without touching project loading, data import, and sidebar panels
separately.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Literal, Optional


TemplateKind = Literal["line", "bar", "scatter", "heatmap"]

GROUP_DATA = "数据导入"
GROUP_STYLE = "风格预设"
GROUP_BASIC = "基础信息"
GROUP_CANVAS = "画布尺寸"
GROUP_FONT = "字体设置"
GROUP_AXES = "坐标轴"
GROUP_LEGEND = "图例"
GROUP_LINE = "线条样式"
GROUP_BAR = "柱状图样式"
GROUP_SCATTER = "散点样式"
GROUP_HEATMAP = "热力图样式"
GROUP_COLORS = "颜色设置"
GROUP_LABELS = "数据标签"
GROUP_CUSTOM_TEXT = "自定义文字位置"
GROUP_EXPORT = "导出设置"

LINE_GROUPS = frozenset(
    {
        GROUP_DATA,
        GROUP_STYLE,
        GROUP_BASIC,
        GROUP_CANVAS,
        GROUP_FONT,
        GROUP_AXES,
        GROUP_LEGEND,
        GROUP_LINE,
        GROUP_COLORS,
        GROUP_LABELS,
        GROUP_CUSTOM_TEXT,
        GROUP_EXPORT,
    }
)
BAR_GROUPS = frozenset(
    {
        GROUP_DATA,
        GROUP_STYLE,
        GROUP_BASIC,
        GROUP_CANVAS,
        GROUP_FONT,
        GROUP_AXES,
        GROUP_LEGEND,
        GROUP_BAR,
        GROUP_COLORS,
        GROUP_LABELS,
        GROUP_EXPORT,
    }
)
HEATMAP_GROUPS = frozenset(
    {
        GROUP_DATA,
        GROUP_STYLE,
        GROUP_BASIC,
        GROUP_CANVAS,
        GROUP_FONT,
        GROUP_AXES,
        GROUP_HEATMAP,
        GROUP_EXPORT,
    }
)
SCATTER_GROUPS = frozenset(
    {
        GROUP_DATA,
        GROUP_STYLE,
        GROUP_BASIC,
        GROUP_CANVAS,
        GROUP_FONT,
        GROUP_AXES,
        GROUP_LEGEND,
        GROUP_SCATTER,
        GROUP_COLORS,
        GROUP_EXPORT,
    }
)


@dataclass(frozen=True)
class TemplateSpec:
    id: str
    display_name: str
    kind: TemplateKind
    simple_groups: FrozenSet[str]
    legacy: bool = False


TEMPLATE_SPECS: Dict[str, TemplateSpec] = {
    "line_chart_basic": TemplateSpec(
        id="line_chart_basic",
        display_name="基础折线图",
        kind="line",
        simple_groups=LINE_GROUPS,
    ),
    "line_chart_report": TemplateSpec(
        id="line_chart_report",
        display_name="报告风格多折线图",
        kind="line",
        simple_groups=LINE_GROUPS,
    ),
    "bar_chart_basic": TemplateSpec(
        id="bar_chart_basic",
        display_name="基础柱状图",
        kind="bar",
        simple_groups=BAR_GROUPS,
    ),
    "horizontal_bar_chart": TemplateSpec(
        id="horizontal_bar_chart",
        display_name="横向柱状图",
        kind="bar",
        simple_groups=BAR_GROUPS - {GROUP_LEGEND},
    ),
    "heatmap_basic": TemplateSpec(
        id="heatmap_basic",
        display_name="基础热力图",
        kind="heatmap",
        simple_groups=HEATMAP_GROUPS,
    ),
    "scatter_chart_basic": TemplateSpec(
        id="scatter_chart_basic",
        display_name="基础散点图",
        kind="scatter",
        simple_groups=SCATTER_GROUPS,
    ),
    "line_chart": TemplateSpec(
        id="line_chart",
        display_name="多折线图（旧版 · 兼容）",
        kind="line",
        simple_groups=LINE_GROUPS - {GROUP_LABELS, GROUP_CUSTOM_TEXT},
        legacy=True,
    ),
}

DEFAULT_TEMPLATE_IDS: List[str] = [
    "line_chart_basic",
    "line_chart_report",
    "bar_chart_basic",
    "horizontal_bar_chart",
    "heatmap_basic",
    "scatter_chart_basic",
]


def get_template_spec(template_id: str) -> Optional[TemplateSpec]:
    return TEMPLATE_SPECS.get(template_id)


def get_template_display_name(template_id: str) -> str:
    spec = get_template_spec(template_id)
    return spec.display_name if spec else template_id


def get_template_kind(template_id: str) -> Optional[TemplateKind]:
    spec = get_template_spec(template_id)
    return spec.kind if spec else None


def get_simple_groups(template_id: str) -> Optional[FrozenSet[str]]:
    spec = get_template_spec(template_id)
    return spec.simple_groups if spec else None
