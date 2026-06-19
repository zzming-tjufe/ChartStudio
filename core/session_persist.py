"""
会话持久化 — 刷新浏览器后恢复上次打开的项目。

Streamlit 的 session_state 仅在当前浏览器会话内有效，刷新页面会丢失。
本模块将「最近打开的项目路径」写入用户目录，并在启动时自动恢复。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import quote, unquote

import streamlit as st

PERSIST_DIR = Path.home() / ".chartstudio"
SESSION_FILE = PERSIST_DIR / "session.json"
QUERY_PARAM = "project"


def _normalize_path(path: str) -> str:
    return str(Path(path).expanduser().resolve())


def save_session_snapshot(project_path: str, panel_mode: str = "简洁模式") -> None:
    """保存当前打开的项目路径（及少量 UI 偏好）。"""
    try:
        PERSIST_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "project_path": _normalize_path(project_path),
            "panel_mode": panel_mode,
        }
        SESSION_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def load_session_snapshot() -> Optional[Dict[str, Any]]:
    if not SESSION_FILE.is_file():
        return None
    try:
        data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("project_path"):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return None


def clear_session_snapshot() -> None:
    try:
        if SESSION_FILE.is_file():
            SESSION_FILE.unlink()
    except OSError:
        pass


def sync_project_query_param(project_path: str) -> None:
    """将项目路径写入 URL，便于刷新后在同一会话策略下恢复。"""
    try:
        st.query_params[QUERY_PARAM] = quote(_normalize_path(project_path), safe="")
    except Exception:
        pass


def clear_project_query_param() -> None:
    try:
        if QUERY_PARAM in st.query_params:
            del st.query_params[QUERY_PARAM]
    except Exception:
        pass


def resolve_restore_path() -> Optional[str]:
    """优先 URL 参数，其次本地会话文件。"""
    raw_qp = st.query_params.get(QUERY_PARAM)
    if raw_qp:
        candidate = unquote(str(raw_qp))
        root = Path(candidate).expanduser()
        if root.is_dir():
            return _normalize_path(candidate)

    snap = load_session_snapshot()
    if snap:
        candidate = str(snap.get("project_path", ""))
        if candidate and Path(candidate).is_dir():
            return _normalize_path(candidate)

    return None
