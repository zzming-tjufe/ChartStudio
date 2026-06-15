"""
配置差异比较工具 — 支持中文字段名的人性化改动记录。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from core.config_utils import flatten_dict
from core.field_labels import get_field_label


@dataclass
class ConfigChange:
    path: str
    label: str
    old_value: Any
    new_value: Any

    def to_display(self) -> str:
        return f"{self.label}：{_format_value(self.old_value)} → {_format_value(self.new_value)}"

    def to_technical(self) -> str:
        return f"{self.path}: {_format_value(self.old_value)} → {_format_value(self.new_value)}"


def _format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, list):
        return str(value)
    return str(value)


def compare_configs(
    base: Dict[str, Any],
    current: Dict[str, Any],
    human_readable: bool = True,
) -> List[str]:
    """
    比较两份配置，返回改动描述列表。

    human_readable=True 时使用中文字段名。
    """
    changes = compare_config_changes(base, current)
    if human_readable:
        return [c.to_display() for c in changes]
    return [c.to_technical() for c in changes]


def compare_config_changes(
    base: Dict[str, Any],
    current: Dict[str, Any],
) -> List[ConfigChange]:
    flat_base = flatten_dict(base)
    flat_current = flatten_dict(current)
    all_keys = sorted(set(flat_base.keys()) | set(flat_current.keys()))
    changes: List[ConfigChange] = []

    for key in all_keys:
        if key not in flat_base or key not in flat_current:
            continue
        old_val = flat_base[key]
        new_val = flat_current[key]
        if old_val != new_val:
            changes.append(
                ConfigChange(
                    path=key,
                    label=get_field_label(key),
                    old_value=old_val,
                    new_value=new_val,
                )
            )
    return changes


def has_changes(base: Dict[str, Any], current: Dict[str, Any]) -> bool:
    return len(compare_config_changes(base, current)) > 0
