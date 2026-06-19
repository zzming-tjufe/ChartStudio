"""字段下拉选项 — 供 semantic_widgets 与 config_validator 共用。"""

from __future__ import annotations

from typing import Dict, List

from core.heatmap_cmaps import cmap_ids

SELECT_FIELD_OPTIONS: Dict[str, List[str]] = {
    "legend.loc": [
        "best",
        "upper right",
        "upper left",
        "lower left",
        "lower right",
        "right",
        "center left",
        "center right",
        "lower center",
        "upper center",
        "center",
    ],
    "line_style.marker": [
        "o",
        "s",
        "^",
        "v",
        "D",
        "d",
        "P",
        "X",
        "*",
        "h",
        "H",
        "+",
        "x",
        "None",
    ],
    "heatmap.cmap": cmap_ids(),
}
