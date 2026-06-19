"""数据标签格式化 — 各模板统一调用。"""

from __future__ import annotations

from typing import Any, Dict, Union


def format_data_label(value: Any, label_cfg: Dict[str, Any] | None = None) -> str:
    """
    按 data_labels 配置格式化数值标签。

    支持 decimals、prefix、suffix。
    """
    cfg = label_cfg if isinstance(label_cfg, dict) else {}
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)

    decimals = cfg.get("decimals", 1)
    try:
        decimals_int = max(0, int(decimals))
    except (TypeError, ValueError):
        decimals_int = 1

    prefix = str(cfg.get("prefix", "") or "")
    suffix = str(cfg.get("suffix", "") or "")
    formatted = f"{num:.{decimals_int}f}"
    return f"{prefix}{formatted}{suffix}"
