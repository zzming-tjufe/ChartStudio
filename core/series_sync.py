"""
series 配置同步 — 导入新 data 后重建 series（保留 overall）。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.data_keys import category_series_key, unique_key

LINE_PALETTE = ["#1565C0", "#E53935", "#43A047", "#FB8C00", "#8E24AA", "#00897B"]
SCATTER_PALETTE = ["#5E35B1", "#00897B", "#E53935", "#FB8C00"]
BAR_PALETTE = ["#1976D2", "#388E3C", "#F57C00", "#7B1FA2", "#0097A7", "#C62828"]


def rebuild_series_config(
    config: dict,
    data: dict,
    template_id: str,
    labels_map: Optional[Dict[str, str]] = None,
) -> dict:
    """
    清理旧的具体系列配置，仅保留 series.overall，再按新 data 重建。
    labels_map: data key -> 原始列名/分组名（用于 label 显示）
    """
    labels_map = labels_map or {}
    old = config.get("series", {}) if isinstance(config.get("series"), dict) else {}
    overall = old.get("overall")
    new_series: Dict[str, Any] = {}
    if isinstance(overall, dict):
        new_series["overall"] = overall

    if template_id in ("line_chart_basic", "line_chart_report", "line_chart"):
        keys = [k for k in data if k != "x"]
        for i, key in enumerate(keys):
            label = labels_map.get(key, key)
            prev = old.get(key, {}) if isinstance(old.get(key), dict) else {}
            new_series[key] = {
                "color": prev.get("color", LINE_PALETTE[i % len(LINE_PALETTE)]),
                "label": label,
            }
            if "label_offset" in prev:
                new_series[key]["label_offset"] = prev["label_offset"]

    elif template_id == "scatter_chart_basic":
        keys = [k for k in data if isinstance(data.get(k), dict)]
        for i, key in enumerate(keys):
            label = labels_map.get(key, str(key))
            prev = old.get(key, {}) if isinstance(old.get(key), dict) else {}
            new_series[key] = {
                "color": prev.get("color", SCATTER_PALETTE[i % len(SCATTER_PALETTE)]),
                "label": label,
            }

    elif template_id in ("bar_chart_basic", "horizontal_bar_chart"):
        cats = data.get("categories", [])
        if isinstance(cats, list):
            for i, cat in enumerate(cats):
                key = category_series_key(str(cat))
                prev = old.get(key, {}) if isinstance(old.get(key), dict) else {}
                new_series[key] = {
                    "color": prev.get("color", BAR_PALETTE[i % len(BAR_PALETTE)]),
                    "label": str(cat),
                }

    config["series"] = new_series
    return config


def assign_line_keys(y_col_names: list[str]) -> tuple[dict[str, str], dict[str, str]]:
    """y 列名 -> data key；data key -> 原始列名 label。"""
    used: set[str] = set()
    reserved = {"x"}
    col_to_key: dict[str, str] = {}
    key_to_label: dict[str, str] = {}
    for col in y_col_names:
        key = unique_key(col, used, reserved=reserved)
        col_to_key[col] = key
        key_to_label[key] = col
    return col_to_key, key_to_label


def assign_group_keys(group_names: list) -> tuple[dict[Any, str], dict[str, str]]:
    used: set[str] = set()
    name_to_key: dict[Any, str] = {}
    key_to_label: dict[str, str] = {}
    for name in group_names:
        key = unique_key(str(name), used)
        name_to_key[name] = key
        key_to_label[key] = str(name)
    return name_to_key, key_to_label
