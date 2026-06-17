"""
未保存修改保护 — 破坏性操作前确认。
"""

from __future__ import annotations

from typing import Callable, Dict

import streamlit as st

PENDING_KEY = "cs_pending_action"


def set_pending_action(action_id: str) -> None:
    st.session_state[PENDING_KEY] = action_id


def clear_pending_action() -> None:
    st.session_state.pop(PENDING_KEY, None)


def get_pending_action() -> Optional[str]:
    return st.session_state.get(PENDING_KEY)


def render_unsaved_confirm(
    action_id: str,
    *,
    message: str = "当前有未保存的修改。丢弃后将无法恢复。",
) -> Optional[bool]:
    """
    若 action_id 为待确认操作，渲染确认 UI。
    返回 True=继续, False=取消, None=非此 action 或未在确认态。
    """
    if get_pending_action() != action_id:
        return None

    st.warning(message)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("丢弃并继续", key=f"confirm_discard_{action_id}", type="primary"):
            clear_pending_action()
            return True
    with c2:
        if st.button("取消", key=f"confirm_cancel_{action_id}"):
            clear_pending_action()
            return False
    return False  # 仍在等待用户选择


def resolve_pending_action(callbacks: Dict[str, Callable[..., None]]) -> bool:
    """
    若存在待确认操作，渲染确认 UI。
    callbacks 键：close_project / reload_project / reset_config / open（接收 path 参数）
    """
    pending = get_pending_action()
    if not pending:
        return False

    verdict = render_unsaved_confirm(pending)
    if verdict is True:
        clear_pending_action()
        if pending.startswith("open:"):
            open_fn = callbacks.get("open")
            if open_fn:
                open_fn(pending[5:])
        else:
            fn = callbacks.get(pending)
            if fn:
                fn()
    return True


def request_guarded_action(action_id: str, unsaved: bool, proceed: Callable[[], None]) -> None:
    """按钮点击：有未保存则进入确认，否则直接执行。"""
    if get_pending_action():
        return
    if unsaved:
        set_pending_action(action_id)
        st.rerun()
    else:
        proceed()
