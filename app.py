"""
ChartStudio — 科研图表可视化调参工具

Streamlit 主入口。
"""

from __future__ import annotations

import sys
import traceback
import hashlib
import json
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st

APP_ROOT = Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from core.ai_prompt import get_ai_prompt
from core.app_state import get_app_state
from core.config_loader import deep_copy_config, load_yaml, save_yaml, strip_internal_keys
from core.config_migrate import normalize_config
from core.config_utils import get_by_path, _MISSING
from core.diff_utils import has_changes
from core.dynamic_importer import import_draw_chart
from core.font_runtime import apply_chart_fonts, pop_font_fallback_warning, prepare_chart_fonts
from core.project_manager import create_project, validate_project
from core.session_persist import (
    clear_project_query_param,
    clear_session_snapshot,
    load_session_snapshot,
    resolve_restore_path,
    save_session_snapshot,
    sync_project_query_param,
)
from core.session_utils import clear_config_widget_state, get_project_widget_prefix, sync_widget_scope
from core.unsaved_guard import request_guarded_action, resolve_pending_action
from core.ui_editor import (
    render_editor_actions,
    render_editor_footer,
    render_editor_preview,
    render_editor_sidebar,
)
from core.ui_welcome import render_welcome_main, render_welcome_sidebar


def _sidebar_initial_state():
    try:
        parts = tuple(int(x) for x in st.__version__.split(".")[:3] if x.isdigit())
    except ValueError:
        parts = (1, 0, 0)
    if parts >= (1, 53, 0):
        return 360
    return "expanded"


def _ensure_sidebar_visible_once() -> None:
    if st.session_state.get("_sidebar_visible_once"):
        return
    st.session_state._sidebar_visible_once = True
    import streamlit.components.v1 as components

    components.html(
        """
        <script>
        (function () {
            const doc = window.parent.document;
            const sidebar = doc.querySelector('[data-testid="stSidebar"]');
            if (!sidebar || sidebar.getAttribute('aria-expanded') === 'true') return;
            const btn =
                doc.querySelector('[data-testid="stExpandSidebarButton"]') ||
                doc.querySelector('[data-testid="collapsedControl"]') ||
                doc.querySelector('button[kind="headerNoPadding"]');
            if (btn) btn.click();
        })();
        </script>
        """,
        height=0,
        width=0,
    )


st.set_page_config(
    page_title="ChartStudio",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state=_sidebar_initial_state(),
)

st.markdown(
    """
    <style>
    .cs-header { padding: 0.2rem 0 0.8rem 0; border-bottom: 1px solid #e6e6e6; margin-bottom: 1rem; }
    .cs-badge-ok { background:#e8f5e9; color:#2e7d32; padding:4px 10px; border-radius:999px; font-size:0.85rem; }
    .cs-badge-warn { background:#fff3e0; color:#e65100; padding:4px 10px; border-radius:999px; font-size:0.85rem; }
    .cs-badge-muted { background:#f5f5f5; color:#616161; padding:4px 10px; border-radius:999px; font-size:0.85rem; }
    .cs-meta { font-size:0.85rem; color:#666; line-height:1.6; }
    .cs-path-ok { background:#e8f5e9; color:#2e7d32; padding:8px 12px; border-radius:6px; font-size:0.9rem; margin:6px 0; }
    .cs-path-warn { background:#fff3e0; color:#e65100; padding:8px 12px; border-radius:6px; font-size:0.9rem; margin:6px 0; }
    .cs-path-error { background:#ffebee; color:#c62828; padding:8px 12px; border-radius:6px; font-size:0.9rem; margin:6px 0; }
    div[data-testid="stExpander"] details summary p { font-weight: 600; }
    [data-testid="stSidebar"][aria-expanded="true"] {
        width: 22rem !important;
        min-width: 22rem !important;
        transform: none !important;
    }
    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
        width: 22rem !important;
        min-width: 22rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        padding: 1rem 1rem 1.5rem;
        width: 100%;
        box-sizing: border-box;
    }
    [data-testid="stFileUploader"] section[data-testid="stFileUploadDropzone"] {
        border: 2px dashed #90caf9;
        border-radius: 8px;
        background: #f8fbff;
    }
    [data-testid="stFileUploader"] section[data-testid="stFileUploadDropzone"]:hover {
        border-color: #1565C0;
        background: #eef5ff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _init_session_state() -> None:
    defaults = {
        "project_info": None,
        "base_config": None,
        "current_config": None,
        "draw_chart_fn": None,
        "last_error": None,
        "last_error_trace": None,
        "render_error": None,
        "render_trace": None,
        "render_status": None,
        "last_render_fingerprint": None,
        "last_render_succeeded": False,
        "status_message": None,
        "panel_mode": "简洁模式",
        "open_path_input": "",
        "new_path_input": "",
        "migration_notes": [],
        "font_fallback_warning": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


OPEN_PATH_WIDGET_KEYS = (
    "open_path_input",
    "main_open_path_input",
    "sidebar_open_path_input",
    "sidebar_open_path",
)

NEW_PATH_WIDGET_KEYS = (
    "new_path_input",
    "main_new_path_input",
    "sidebar_new_path_input",
    "sidebar_new_path",
)


def _apply_pending_widget_values() -> None:
    if "open_path_sync" in st.session_state:
        val = st.session_state.pop("open_path_sync")
        for key in OPEN_PATH_WIDGET_KEYS:
            st.session_state[key] = val
    if "new_path_sync" in st.session_state:
        val = st.session_state.pop("new_path_sync")
        for key in NEW_PATH_WIDGET_KEYS:
            st.session_state[key] = val


def _queue_open_path(value: str) -> None:
    st.session_state.open_path_sync = value


def _queue_new_path(value: str) -> None:
    st.session_state.new_path_sync = value


_init_session_state()
_apply_pending_widget_values()


def _load_project(project_path: str) -> None:
    ok, msg, info = validate_project(project_path)
    if not ok or info is None:
        st.session_state.last_error = msg
        st.session_state.last_error_trace = None
        st.session_state.status_message = None
        st.session_state.render_status = "error"
        return

    try:
        raw_config = load_yaml(info.config_path)
        config, migration_notes = normalize_config(raw_config, template_id=info.template_id)
        draw_fn = import_draw_chart(info.core_path)
    except Exception as exc:
        st.session_state.last_error = f"项目加载失败：{exc}"
        st.session_state.last_error_trace = traceback.format_exc()
        st.session_state.status_message = None
        st.session_state.render_status = "error"
        return

    sync_widget_scope(str(info.root))
    st.session_state.project_info = info
    st.session_state.base_config = deep_copy_config(config)
    st.session_state.current_config = deep_copy_config(config)
    st.session_state.draw_chart_fn = draw_fn
    st.session_state.last_error = None
    st.session_state.last_error_trace = None
    st.session_state.render_error = None
    st.session_state.render_trace = None
    st.session_state.render_status = None
    st.session_state.last_render_fingerprint = None
    st.session_state.last_render_succeeded = False
    st.session_state.migration_notes = migration_notes
    if migration_notes:
        st.session_state.status_message = (
            f"{msg}（已自动兼容旧版配置结构，保存后将写入新格式）"
        )
    else:
        st.session_state.status_message = msg
    _queue_open_path(str(info.root))
    save_session_snapshot(str(info.root), st.session_state.get("panel_mode", "简洁模式"))
    sync_project_query_param(str(info.root))


def _try_restore_session() -> None:
    """刷新页面后，从本地文件或 URL 参数恢复上次打开的项目。"""
    if st.session_state.get("project_info"):
        return
    if st.session_state.get("_session_restore_done"):
        return
    st.session_state._session_restore_done = True

    path = resolve_restore_path()
    if not path:
        return

    _load_project(path)
    if st.session_state.project_info:
        snap = load_session_snapshot()
        if snap and snap.get("panel_mode") in ("简洁模式", "高级模式"):
            st.session_state.panel_mode = snap["panel_mode"]
        sync_project_query_param(path)
        if not st.session_state.get("status_message"):
            st.session_state.status_message = "已恢复上次打开的项目"
    else:
        clear_session_snapshot()
        clear_project_query_param()


def _close_project() -> None:
    """关闭当前项目，返回欢迎页。"""
    clear_session_snapshot()
    clear_project_query_param()
    clear_config_widget_state()
    st.session_state.project_info = None
    st.session_state.base_config = None
    st.session_state.current_config = None
    st.session_state.draw_chart_fn = None
    st.session_state.render_error = None
    st.session_state.render_trace = None
    st.session_state.render_status = None
    st.session_state.last_render_fingerprint = None
    st.session_state.last_render_succeeded = False
    st.session_state.migration_notes = []
    st.session_state.status_message = "已关闭项目"
    st.session_state.last_error = None
    st.session_state._session_restore_done = True
    st.rerun()


def _try_create_project(path: str, template_name: str, project_name: str | None = None) -> None:
    ok, msg, info = create_project(path, template_name=template_name, project_name=project_name)
    if ok and info:
        _load_project(str(info.root))
        st.session_state.status_message = msg
        st.rerun()
    else:
        st.session_state.last_error = msg


def _handle_reset_confirmed() -> None:
    if not _unsaved():
        st.session_state.status_message = "当前配置与已保存版本一致"
        st.rerun()
        return
    _reset_to_saved_config()
    st.session_state.status_message = "已恢复为上次保存的配置"
    st.rerun()


def _restore_snapshot_to_session(data: dict) -> None:
    clear_config_widget_state()
    st.session_state.current_config = deep_copy_config(data)


def _request_open(path: str) -> None:
    path = path.strip()
    if not path:
        return
    current = (
        str(st.session_state.project_info.root)
        if st.session_state.project_info
        else ""
    )
    if path == current:
        return

    def proceed() -> None:
        _load_project(path)
        st.rerun()

    request_guarded_action(f"open:{path}", _unsaved(), proceed)


def _request_close() -> None:
    request_guarded_action("close_project", _unsaved(), _close_project)


def _request_reload() -> None:
    info = st.session_state.project_info
    if info is None:
        return

    def proceed() -> None:
        _load_project(str(info.root))
        st.rerun()

    request_guarded_action("reload_project", _unsaved(), proceed)


def _request_reset() -> None:
    request_guarded_action("reset_config", _unsaved(), _handle_reset_confirmed)


def _handle_open(path: str) -> None:
    _request_open(path)


def _reload_draw_chart() -> None:
    info = st.session_state.project_info
    if info is None:
        return
    st.session_state.draw_chart_fn = import_draw_chart(info.core_path)


def _reset_to_saved_config() -> None:
    info = st.session_state.project_info
    if info is None or st.session_state.base_config is None:
        return
    clear_config_widget_state()
    st.session_state.current_config = deep_copy_config(st.session_state.base_config)


def _prepare_render_config(config: dict) -> dict:
    render_cfg = deep_copy_config(config)
    info = st.session_state.project_info
    if info:
        render_cfg["_project_root"] = str(info.root)
    return render_cfg


def _config_fingerprint(config: dict) -> str:
    payload = json.dumps(
        strip_internal_keys(config),
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _get_export_settings(config: dict) -> tuple[int | None, bool]:
    dpi_val = get_by_path(config, "export.dpi")
    if dpi_val is _MISSING:
        dpi_val = get_by_path(config, "chart.dpi")
    dpi_int = int(dpi_val) if dpi_val is not _MISSING else None
    transparent_val = get_by_path(config, "export.transparent")
    transparent = bool(transparent_val) if transparent_val is not _MISSING else False
    return dpi_int, transparent


def _render_chart(config: dict):
    draw_fn = st.session_state.draw_chart_fn
    if draw_fn is None:
        return None

    fingerprint = _config_fingerprint(config)
    render_cfg = _prepare_render_config(config)
    font_bundle = prepare_chart_fonts(render_cfg)
    try:
        fig = draw_fn(render_cfg)
        st.session_state.font_fallback_warning = pop_font_fallback_warning(render_cfg)
        if fig is None:
            st.session_state.render_error = "绘图函数未返回有效图表，请检查绘图核心文件。"
            st.session_state.render_trace = None
            st.session_state.render_status = "error"
            st.session_state.last_render_fingerprint = fingerprint
            st.session_state.last_render_succeeded = False
            return None
        apply_chart_fonts(fig, render_cfg)
        st.session_state.render_error = None
        st.session_state.render_trace = None
        st.session_state.render_status = "success"
        st.session_state.last_render_fingerprint = fingerprint
        st.session_state.last_render_succeeded = True
        _, transparent = _get_export_settings(config)
        if transparent:
            fig.patch.set_alpha(0.0)
            for ax in fig.get_axes():
                ax.patch.set_alpha(0.0)
        return fig
    except Exception as exc:
        st.session_state.render_error = f"图表渲染失败：{type(exc).__name__} — {exc}"
        st.session_state.render_trace = traceback.format_exc()
        st.session_state.render_status = "error"
        st.session_state.last_render_fingerprint = fingerprint
        st.session_state.last_render_succeeded = False
        return None


def _render_probe_for_save(config: dict):
    if (
        st.session_state.get("last_render_succeeded")
        and st.session_state.get("last_render_fingerprint") == _config_fingerprint(config)
    ):
        return True
    return _render_chart(config)


def _get_canvas_size(config: dict) -> str:
    w = get_by_path(config, "figure.width")
    h = get_by_path(config, "figure.height")
    if w is _MISSING:
        w = get_by_path(config, "chart.width")
    if h is _MISSING:
        h = get_by_path(config, "chart.height")
    if w is _MISSING or h is _MISSING:
        return "—"
    return f"{float(w):.1f} × {float(h):.1f} 英寸"


def _get_export_dpi(config: dict) -> str:
    dpi = get_by_path(config, "export.dpi")
    if dpi is _MISSING:
        dpi = get_by_path(config, "chart.dpi")
    return str(int(dpi)) if dpi is not _MISSING else "—"


def _unsaved() -> bool:
    if not st.session_state.base_config or not st.session_state.current_config:
        return False
    return has_changes(st.session_state.base_config, st.session_state.current_config)


def _save_config() -> None:
    info = st.session_state.project_info
    if info is None:
        return
    try:
        save_yaml(info.config_path, st.session_state.current_config)
        st.session_state.base_config = deep_copy_config(st.session_state.current_config)
        st.session_state.migration_notes = []
        st.session_state.status_message = "配置已保存到图表配置文件"
        st.rerun()
    except Exception as exc:
        st.session_state.last_error = f"保存失败：{exc}"
        st.session_state.last_error_trace = traceback.format_exc()


def _save_snapshot() -> None:
    info = st.session_state.project_info
    if info is None:
        return
    try:
        configs_dir = info.root / "configs"
        configs_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_path = configs_dir / f"chart_config_{ts}.yaml"
        save_yaml(snapshot_path, st.session_state.current_config)
        st.session_state.status_message = f"配置快照已保存：{snapshot_path.name}"
        st.rerun()
    except Exception as exc:
        st.error(f"快照保存失败：{exc}")


def _save_migrated() -> None:
    info = st.session_state.project_info
    if info is None:
        return
    try:
        save_yaml(info.config_path, st.session_state.current_config)
        st.session_state.base_config = deep_copy_config(st.session_state.current_config)
        st.session_state.migration_notes = []
        st.session_state.status_message = "配置结构已升级并保存"
        st.rerun()
    except Exception as exc:
        st.session_state.last_error = f"升级保存失败：{exc}"


def _handle_reset() -> None:
    _request_reset()


def _handle_reload_core() -> None:
    try:
        _reload_draw_chart()
        st.session_state.status_message = "已重新加载绘图核心文件"
        st.rerun()
    except Exception as exc:
        st.session_state.last_error = f"重载绘图核心失败：{exc}"


# ---------------------------------------------------------------------------
# 侧栏（先于主区域，以便 current_config 在本轮 run 内更新）
# ---------------------------------------------------------------------------
_try_restore_session()

with st.sidebar:
    _sidebar_app_state = get_app_state(st.session_state)
    if _sidebar_app_state == "welcome":
        render_welcome_sidebar(
            on_queue_open_path=_queue_open_path,
            on_queue_new_path=_queue_new_path,
            on_open=_handle_open,
            on_create=_try_create_project,
        )
    elif st.session_state.project_info:
        _info_sidebar = st.session_state.project_info
        resolve_pending_action(
            {
                "close_project": _close_project,
                "reload_project": lambda: (_load_project(str(_info_sidebar.root)), st.rerun()),
                "reset_config": _handle_reset_confirmed,
                "open": lambda p: (_load_project(p), st.rerun()),
            }
        )
        render_editor_sidebar(
            _info_sidebar,
            widget_prefix=get_project_widget_prefix(str(_info_sidebar.root)),
            unsaved=_unsaved(),
            on_load=_handle_open,
            on_create=lambda path, tpl, name=None: _try_create_project(path, tpl, name),
            on_reload=_request_reload,
            on_reload_core=_handle_reload_core,
            on_reset=_request_reset,
            on_save_migrated=_save_migrated,
            on_close_project=_request_close,
            on_queue_open_path=_queue_open_path,
            on_queue_new_path=_queue_new_path,
        )
        save_session_snapshot(
            str(_info_sidebar.root), st.session_state.get("panel_mode", "简洁模式")
        )

_ensure_sidebar_visible_once()

# 侧栏可能已更新 current_config，主区域必须使用最新值
info = st.session_state.project_info
cfg = st.session_state.current_config
app_state = get_app_state(st.session_state)

# ---------------------------------------------------------------------------
# 顶部
# ---------------------------------------------------------------------------
header_l, header_r = st.columns([3, 2])
with header_l:
    st.markdown("## 📊 ChartStudio")
    if app_state == "welcome":
        st.caption("选择模板或打开项目，开始制作论文 / 报告图表")
    else:
        st.caption("导入数据、调整样式、实时预览、一键导出")

with header_r:
    if info:
        if _unsaved():
            st.markdown(
                '<span class="cs-badge-warn">● 有未保存的修改</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span class="cs-badge-ok">● 配置已同步</span>',
                unsafe_allow_html=True,
            )
        st.markdown(
            f'<div class="cs-meta">当前项目：<b>{info.display_name}</b><br>'
            f'模板：{info.template_name}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="cs-badge-muted">欢迎使用</span>',
            unsafe_allow_html=True,
        )

if app_state == "editing" and _unsaved():
    st.warning("您有未保存的样式修改，请记得点击「保存当前配置」。")

if st.session_state.status_message:
    st.info(f"最近操作：{st.session_state.status_message}")

if st.session_state.last_error:
    st.error(st.session_state.last_error)

st.markdown('<div class="cs-header"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 主区域（按状态）
# ---------------------------------------------------------------------------
if app_state == "welcome":
    render_welcome_main(
        on_queue_open_path=_queue_open_path,
        on_queue_new_path=_queue_new_path,
        on_open=_handle_open,
        on_create=_try_create_project,
    )
    with st.expander("让 AI 从零创建 ChartStudio 项目", expanded=False):
        st.markdown("尚未打开项目时，可使用下方通用提示词创建兼容项目。")
        st.code(get_ai_prompt(), language="text")
        st.download_button(
            "下载通用创建提示词",
            data=get_ai_prompt(),
            file_name="chartstudio_ai_create_prompt.txt",
            mime="text/plain",
            use_container_width=True,
        )

elif app_state == "loading":
    st.info("正在加载项目…")

elif app_state == "editing" and info and cfg:
    render_editor_preview(
        info,
        cfg,
        unsaved=_unsaved(),
        get_canvas_size=_get_canvas_size,
        get_export_dpi=_get_export_dpi,
        get_export_settings=_get_export_settings,
        render_chart=_render_chart,
    )
    render_editor_actions(
        info,
        cfg,
        unsaved=_unsaved(),
        get_export_settings=_get_export_settings,
        render_chart=_render_chart,
        render_probe=_render_probe_for_save,
        on_save=_save_config,
        on_snapshot=_save_snapshot,
        on_reset=_request_reset,
        on_restore_snapshot=_restore_snapshot_to_session,
    )
    render_editor_footer(info, unsaved=_unsaved())
