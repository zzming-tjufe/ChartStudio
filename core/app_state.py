"""
应用状态 — 根据 session 推导当前界面阶段。
"""

from __future__ import annotations

from typing import Literal

AppState = Literal["welcome", "editing", "loading"]


def get_app_state(session) -> AppState:
    """从 session_state 推导界面状态。渲染错误不改变页面结构，仅在预览区内展示。"""
    if not session.get("project_info"):
        return "welcome"
    if session.get("current_config") and session.get("draw_chart_fn"):
        return "editing"
    return "loading"
