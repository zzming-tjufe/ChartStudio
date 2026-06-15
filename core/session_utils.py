"""Streamlit session state 工具 — 切换项目时清理控件状态。"""

from __future__ import annotations

import hashlib
from typing import Optional

import streamlit as st

# 参数控件 key 的特征片段
_WIDGET_MARKERS = ("_simple_", "_adv_", "_cfg_")


def get_project_widget_prefix(project_root: Optional[str] = None) -> str:
    """根据项目路径生成控件 key 前缀，避免项目间状态污染。"""
    root = project_root or (
        str(st.session_state.project_info.root)
        if st.session_state.get("project_info")
        else "default"
    )
    digest = hashlib.md5(root.encode("utf-8")).hexdigest()[:8]
    return f"p{digest}"


def clear_config_widget_state() -> None:
    """清除所有参数面板相关的 widget session state。"""
    to_delete = [
        key
        for key in list(st.session_state.keys())
        if any(marker in key for marker in _WIDGET_MARKERS)
        or key.startswith(("simple_", "adv_", "cfg_"))
    ]
    for key in to_delete:
        del st.session_state[key]


def sync_widget_scope(project_root: str) -> None:
    """项目切换时清理旧 widget 状态。"""
    scope_key = "widget_scope_project"
    if st.session_state.get(scope_key) != project_root:
        clear_config_widget_state()
        st.session_state[scope_key] = project_root
