"""柱状图颜色 — 按 categories 顺序绑定 bar_{safe_key(category)}。"""

from __future__ import annotations

from typing import Any, Dict, List

from core.data_keys import category_series_key


def bar_colors_for_categories(config: Dict[str, Any], categories: List[str]) -> List[str]:
    series_cfg = config.get("series", {}) if isinstance(config.get("series"), dict) else {}
    default = series_cfg.get("overall", {}).get("color", "#1976D2")
    colors: List[str] = []
    for cat in categories:
        key = category_series_key(str(cat))
        entry = series_cfg.get(key, {})
        if isinstance(entry, dict):
            colors.append(entry.get("color", default))
        else:
            colors.append(default)
    return colors
