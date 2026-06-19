"""
数值列转换 — 统计无法解析与缺失，避免静默吞掉异常。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Union

import pandas as pd


@dataclass
class CoercionReport:
    column: str
    invalid_count: int = 0
    missing_count: int = 0
    filled_invalid: int = 0
    filled_missing: int = 0

    @property
    def has_issues(self) -> bool:
        return self.invalid_count > 0 or self.missing_count > 0

    def message(self) -> str:
        parts: List[str] = []
        if self.invalid_count:
            parts.append(f"无法转为数值 {self.invalid_count} 个")
        if self.missing_count:
            parts.append(f"缺失值 {self.missing_count} 个")
        if self.filled_invalid or self.filled_missing:
            filled = self.filled_invalid + self.filled_missing
            parts.append(f"已用 0 填充 {filled} 个位置（请检查源数据）")
        return f"列「{self.column}」：" + "；".join(parts)


@dataclass
class CoercionBundle:
    values: List[Union[float, int]]
    reports: List[CoercionReport] = field(default_factory=list)

    def warnings(self) -> List[str]:
        return [r.message() for r in self.reports if r.has_issues]


def coerce_numeric_column(
    series: pd.Series,
    *,
    column_name: str = "",
    fill_invalid: float = 0.0,
) -> CoercionBundle:
    """将列转为数值列表，并统计 invalid / NaN。"""
    col = column_name or (series.name if series.name is not None else "列")
    raw = series.copy()
    missing_before = int(raw.isna().sum())
    numeric = pd.to_numeric(raw, errors="coerce")
    invalid_count = int((numeric.isna() & raw.notna()).sum())
    missing_after = int(numeric.isna().sum())
    filled_missing = max(0, missing_after - invalid_count)

    report = CoercionReport(
        column=str(col),
        invalid_count=invalid_count,
        missing_count=missing_before,
        filled_invalid=invalid_count,
        filled_missing=filled_missing,
    )
    values = numeric.fillna(fill_invalid).tolist()
    return CoercionBundle(values=values, reports=[report] if report.has_issues else [])


def merge_reports(*bundles: CoercionBundle) -> List[str]:
    msgs: List[str] = []
    for b in bundles:
        msgs.extend(b.warnings())
    return msgs
