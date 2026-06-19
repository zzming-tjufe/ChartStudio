"""热力图色图方案 — 中文说明与校验（配置仍存 Matplotlib cmap 名）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class HeatmapCmapOption:
    id: str
    label: str
    hint: str
    group: str


# 按科研出图场景精选，避免堆砌冷门色图
HEATMAP_CMAP_OPTIONS: List[HeatmapCmapOption] = [
    # 发散色 — 相关矩阵、正负对比
    HeatmapCmapOption(
        "RdYlBu_r",
        "红黄蓝发散",
        "相关矩阵首选，正负对称、论文常用",
        "发散色（正负对比）",
    ),
    HeatmapCmapOption(
        "RdBu_r",
        "红蓝发散",
        "经典红蓝对比，适合相关系数",
        "发散色（正负对比）",
    ),
    HeatmapCmapOption(
        "coolwarm",
        "冷暖发散",
        "红蓝过渡柔和，适合差异矩阵",
        "发散色（正负对比）",
    ),
    HeatmapCmapOption(
        "PiYG",
        "紫绿发散",
        "紫-白-绿，适合生态/环境类对比",
        "发散色（正负对比）",
    ),
    # 顺序色 — 强度、浓度、单方向数值
    HeatmapCmapOption(
        "YlOrRd",
        "黄橙红渐变",
        "由浅到深表示强度升高，适合频次/热度",
        "顺序色（强度递增）",
    ),
    HeatmapCmapOption(
        "YlGnBu",
        "黄绿蓝渐变",
        "清爽明快，适合浓度或覆盖度",
        "顺序色（强度递增）",
    ),
    HeatmapCmapOption(
        "Blues",
        "蓝色渐变",
        "单色由浅到深，简洁专业",
        "顺序色（强度递增）",
    ),
    HeatmapCmapOption(
        "Oranges",
        "橙色渐变",
        "暖色强度图，适合警示/活跃指标",
        "顺序色（强度递增）",
    ),
    HeatmapCmapOption(
        "Greens",
        "绿色渐变",
        "适合增长、覆盖率、植被类指标",
        "顺序色（强度递增）",
    ),
    HeatmapCmapOption(
        "viridis",
        "紫绿黄感知均匀",
        "色觉友好、感知线性，通用科学绘图",
        "顺序色（强度递增）",
    ),
    HeatmapCmapOption(
        "plasma",
        "紫粉黄高对比",
        "对比强烈，适合演示/PPT",
        "顺序色（强度递增）",
    ),
    HeatmapCmapOption(
        "inferno",
        "暗红黄",
        "深色背景下仍清晰，适合大屏展示",
        "顺序色（强度递增）",
    ),
    # 打印 / 无障碍
    HeatmapCmapOption(
        "Greys",
        "灰度",
        "黑白打印、复印友好",
        "打印与无障碍",
    ),
    HeatmapCmapOption(
        "cividis",
        "色盲友好蓝黄",
        "兼顾色盲读者，适合正式出版",
        "打印与无障碍",
    ),
]

_OPTION_BY_ID: Dict[str, HeatmapCmapOption] = {o.id: o for o in HEATMAP_CMAP_OPTIONS}


def cmap_ids() -> List[str]:
    return [o.id for o in HEATMAP_CMAP_OPTIONS]


def get_cmap_option(cmap_id: str) -> Optional[HeatmapCmapOption]:
    return _OPTION_BY_ID.get(str(cmap_id))


def cmap_display_label(cmap_id: str) -> str:
    opt = get_cmap_option(cmap_id)
    if opt:
        return f"{opt.label}（{opt.id}）"
    return str(cmap_id)


def is_valid_cmap(value: str) -> bool:
    return bool(get_cmap_option(value))


def resolve_cmap_name(value: str, default: str = "RdYlBu_r") -> str:
    """解析配置中的 cmap，未知值回退默认。"""
    v = str(value or "").strip()
    if is_valid_cmap(v):
        return v
    return default
