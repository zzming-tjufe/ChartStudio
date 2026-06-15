"""YAML 配置加载与保存。"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict, Union

import yaml

# 运行时注入、不应写入 YAML 的键
INTERNAL_CONFIG_KEYS = ("_project_root", "_font_fallback_warning")


def load_yaml(path: Union[str, Path]) -> Dict[str, Any]:
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"配置文件不存在: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"配置文件根节点必须是字典: {file_path}")
    return data


def strip_internal_keys(config: Dict[str, Any]) -> Dict[str, Any]:
    """保存前移除运行时注入字段。"""
    cleaned = deep_copy_config(config)
    for key in INTERNAL_CONFIG_KEYS:
        cleaned.pop(key, None)
    return cleaned


def save_yaml(path: Union[str, Path], config: Dict[str, Any]) -> Path:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    payload = strip_internal_keys(config)

    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(
            payload,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
    return file_path


def deep_copy_config(config: Dict[str, Any]) -> Dict[str, Any]:
    return copy.deepcopy(config)
