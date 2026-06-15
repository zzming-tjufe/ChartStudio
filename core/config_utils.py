"""
配置字典路径读写工具。

支持 dot notation 访问嵌套 YAML 结构，供简洁模式面板与语义控件使用。
"""

from __future__ import annotations

import copy
import fnmatch
from typing import Any, Dict, List, Optional


def get_by_path(config: Dict[str, Any], path: str) -> Any:
    """读取 config['a']['b']，路径形如 a.b。"""
    keys = path.split(".")
    current: Any = config
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return _MISSING
        current = current[key]
    return current


def set_by_path(config: Dict[str, Any], path: str, value: Any) -> Dict[str, Any]:
    """写入嵌套路径，返回同一 dict（原地修改）。"""
    keys = path.split(".")
    current = config
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value
    return config


def path_exists(config: Dict[str, Any], path: str) -> bool:
    return get_by_path(config, path) is not _MISSING


def flatten_dict(data: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """将嵌套 dict 扁平化为 dot notation。"""
    items: Dict[str, Any] = {}
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else str(key)
        if isinstance(value, dict):
            items.update(flatten_dict(value, new_key, sep=sep))
        else:
            items[new_key] = value
    return items


def find_paths(
    config: Dict[str, Any],
    explicit: Optional[List[str]] = None,
    glob_pattern: Optional[str] = None,
) -> List[str]:
    """
    在配置中查找存在的字段路径。

    explicit: 按顺序返回存在的固定路径
    glob_pattern: 如 series.*.color
    """
    flat = flatten_dict(config)
    found: List[str] = []

    if explicit:
        for path in explicit:
            if path in flat:
                found.append(path)

    if glob_pattern:
        for path in sorted(flat.keys()):
            if fnmatch.fnmatch(path, glob_pattern) and path not in found:
                found.append(path)

    return found


def deep_copy_config(config: Dict[str, Any]) -> Dict[str, Any]:
    return copy.deepcopy(config)


class _Missing:
    pass


_MISSING = _Missing()
