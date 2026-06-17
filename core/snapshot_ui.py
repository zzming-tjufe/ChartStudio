"""配置快照 UI — 列表、恢复、对比、删除。"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict

import streamlit as st
import yaml

from core.config_loader import strip_internal_keys
from core.config_snapshots import (
    compare_snapshot_with_current,
    delete_snapshot,
    list_snapshots,
    load_snapshot,
)


def render_snapshot_manager(
    project_root: Path,
    current_config: Dict,
    *,
    on_restore_to_session: Callable[[dict], None],
    prefix: str = "snap",
) -> None:
    snapshots = list_snapshots(project_root)
    if not snapshots:
        st.caption("暂无配置快照。可使用「另存配置快照」创建。")
        return

    labels = [f"{s.name}  ({s.mtime_label})" for s in snapshots]
    choice = st.selectbox("历史快照", labels, key=f"{prefix}_pick")
    idx = labels.index(choice)
    snap = snapshots[idx]

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("恢复此快照", key=f"{prefix}_restore", use_container_width=True):
            data = load_snapshot(snap.path)
            on_restore_to_session(data)
            st.session_state.status_message = f"已从快照恢复：{snap.name}（未写入磁盘，请保存配置）"
            st.rerun()
    with c2:
        if st.button("对比当前配置", key=f"{prefix}_diff", use_container_width=True):
            st.session_state[f"{prefix}_diff_target"] = str(snap.path)
    with c3:
        if st.button("删除快照", key=f"{prefix}_delete", use_container_width=True):
            delete_snapshot(snap.path)
            st.session_state.status_message = f"已删除快照：{snap.name}"
            st.session_state.pop(f"{prefix}_diff_target", None)
            st.rerun()

    diff_target = st.session_state.get(f"{prefix}_diff_target")
    if diff_target == str(snap.path):
        snap_cfg = load_snapshot(snap.path)
        changes = compare_snapshot_with_current(snap_cfg, current_config)
        st.markdown(f"**与快照 `{snap.name}` 的差异**")
        if changes:
            for line in changes:
                st.markdown(f"- {line}")
        else:
            st.caption("与当前配置一致。")
        with st.expander("快照 YAML 原文"):
            st.code(
                yaml.dump(
                    strip_internal_keys(snap_cfg),
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                ),
                language="yaml",
            )
