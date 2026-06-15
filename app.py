"""
ChartStudio — 科研图表可视化调参工具

Streamlit 主入口。
"""

from __future__ import annotations

import sys
import traceback
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st
import yaml

APP_ROOT = Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from core.ai_prompt import get_ai_prompt
from core.config_loader import deep_copy_config, load_yaml, save_yaml, strip_internal_keys
from core.config_utils import get_by_path
from core.config_utils import _MISSING
from core.diff_utils import compare_configs, has_changes
from core.dynamic_importer import import_draw_chart
from core.exporter import export_figure
from core.config_migrate import normalize_config
from core.project_manager import create_project, get_template_choices, validate_project
from core.session_utils import clear_config_widget_state, get_project_widget_prefix, sync_widget_scope
from core.font_runtime import apply_chart_fonts, pop_font_fallback_warning, prepare_chart_fonts
from core.widget_factory import render_config_panel


def _sidebar_initial_state():
    """Streamlit 1.53+ 支持像素宽度；更早版本用 expanded + CSS。"""
    try:
        parts = tuple(int(x) for x in st.__version__.split(".")[:3] if x.isdigit())
    except ValueError:
        parts = (1, 0, 0)
    if parts >= (1, 53, 0):
        return 360
    return "expanded"


def _ensure_sidebar_visible_once() -> None:
    """首次进入会话时若侧栏被收起，自动展开（默认应为「左侧调参 + 右侧预览」）。"""
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


# ---------------------------------------------------------------------------
# 页面与样式
# ---------------------------------------------------------------------------
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
    .cs-preview-box { border:1px solid #eee; border-radius:8px; padding:12px; background:#fafafa; }
    .cs-meta { font-size:0.85rem; color:#666; line-height:1.6; }
    div[data-testid="stExpander"] details summary p { font-weight: 600; }
    /* 默认布局：左侧侧栏（调参）+ 右侧预览；展开时保证可读宽度 */
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


def _apply_pending_widget_values() -> None:
    """
    在 widget 实例化之前同步路径输入框。

    Streamlit 不允许在 widget 创建后的同一 run 内修改其绑定的 session state key，
    因此通过 *_sync 缓冲键在下一轮渲染前写入。
    """
    if "open_path_sync" in st.session_state:
        st.session_state.open_path_input = st.session_state.pop("open_path_sync")
    if "new_path_sync" in st.session_state:
        st.session_state.new_path_input = st.session_state.pop("new_path_sync")


def _queue_open_path(value: str) -> None:
    st.session_state.open_path_sync = value


def _queue_new_path(value: str) -> None:
    st.session_state.new_path_sync = value


_init_session_state()
_apply_pending_widget_values()


def _pick_folder_dialog(title: str = "选择文件夹") -> str | None:
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory(title=title)
        root.destroy()
        return folder if folder else None
    except Exception:
        return None


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
        config, migration_notes = normalize_config(raw_config)
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
    st.session_state.migration_notes = migration_notes
    if migration_notes:
        st.session_state.status_message = (
            f"{msg}（已自动兼容旧版配置结构，保存后将写入新格式）"
        )
    else:
        st.session_state.status_message = msg
    _queue_open_path(str(info.root))


def _reload_draw_chart() -> None:
    """重新从磁盘加载 chart_core.py。"""
    info = st.session_state.project_info
    if info is None:
        return
    st.session_state.draw_chart_fn = import_draw_chart(info.core_path)


def _reset_to_saved_config() -> None:
    """丢弃未保存改动，恢复为 base_config。"""
    info = st.session_state.project_info
    if info is None or st.session_state.base_config is None:
        return
    clear_config_widget_state()
    st.session_state.current_config = deep_copy_config(st.session_state.base_config)


def _prepare_render_config(config: dict) -> dict:
    """注入运行时字段，不写入 YAML。"""
    render_cfg = deep_copy_config(config)
    info = st.session_state.project_info
    if info:
        render_cfg["_project_root"] = str(info.root)
    return render_cfg


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

    render_cfg = _prepare_render_config(config)
    font_bundle = prepare_chart_fonts(render_cfg)
    try:
        fig = draw_fn(render_cfg)
        st.session_state.font_fallback_warning = pop_font_fallback_warning(render_cfg)
        if fig is None:
            st.session_state.render_error = "绘图函数未返回有效图表，请检查绘图核心文件。"
            st.session_state.render_trace = None
            st.session_state.render_status = "error"
            return None
        apply_chart_fonts(fig, font_bundle, render_cfg.get("font", {}))
        st.session_state.render_error = None
        st.session_state.render_trace = None
        st.session_state.render_status = "success"
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
        return None


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


# ---------------------------------------------------------------------------
# 顶部：标题 + 项目状态 + 未保存提醒
# ---------------------------------------------------------------------------
header_l, header_r = st.columns([3, 2])
with header_l:
    st.markdown("## 📊 ChartStudio")
    st.caption("科研图表可视化调参 — 导入项目、调整样式、实时预览、一键导出")

with header_r:
    if st.session_state.project_info:
        info = st.session_state.project_info
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
            '<span class="cs-badge-muted">尚未打开项目</span>',
            unsafe_allow_html=True,
        )

if _unsaved():
    st.warning("您有未保存的样式修改，请记得点击「保存当前配置」。")

if st.session_state.status_message:
    st.info(f"最近操作：{st.session_state.status_message}")

if st.session_state.last_error:
    st.error(st.session_state.last_error)

st.markdown('<div class="cs-header"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar：项目管理 + 调参面板（独立滚动，主区域图表始终可见）
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 调整图表样式")
    st.caption("左侧调参 · 右侧实时预览")

    if not st.session_state.project_info:
        st.info("请先在下方打开或新建项目。")

        tab_open, tab_new = st.tabs(["打开项目", "新建项目"])

        with tab_open:
            path_input = st.text_input(
                "项目文件夹",
                placeholder=r"D:\projects\my_chart",
                key="open_path_input",
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button("浏览", key="browse_open", use_container_width=True):
                    picked = _pick_folder_dialog("选择 ChartStudio 项目文件夹")
                    if picked:
                        _queue_open_path(picked)
                        st.rerun()
            with c2:
                if st.button("打开", key="load_project", type="primary", use_container_width=True):
                    if path_input.strip():
                        _load_project(path_input.strip())
                        st.rerun()
                    else:
                        st.session_state.last_error = "请先输入或选择项目文件夹"

        with tab_new:
            new_path = st.text_input(
                "保存位置",
                placeholder=r"D:\projects\new_chart",
                key="new_path_input",
            )
            choices = get_template_choices()
            if choices:
                template_ids = [c[0] for c in choices]
                template_labels = {c[0]: c[1] for c in choices}
                template_name = st.selectbox(
                    "图表模板",
                    options=template_ids,
                    format_func=lambda x: template_labels.get(x, x),
                    key="new_template",
                )
            else:
                template_name = "line_chart_basic"
            project_name = st.text_input("项目名称（可选）", key="new_project_name")
            c3, c4 = st.columns(2)
            with c3:
                if st.button("浏览", key="browse_new", use_container_width=True):
                    picked = _pick_folder_dialog("选择新建项目的目标文件夹")
                    if picked:
                        _queue_new_path(picked)
                        st.rerun()
            with c4:
                if st.button("创建", key="create_project", type="primary", use_container_width=True):
                    if new_path.strip():
                        ok, msg, info = create_project(
                            new_path.strip(),
                            template_name=template_name,
                            project_name=project_name or None,
                        )
                        if ok and info:
                            _load_project(str(info.root))
                            st.session_state.status_message = msg
                            st.rerun()
                        else:
                            st.session_state.last_error = msg
                    else:
                        st.session_state.last_error = "请先输入新建项目的保存位置"
    else:
        info = st.session_state.project_info
        widget_prefix = get_project_widget_prefix(str(info.root))

        with st.expander("项目管理", expanded=False):
            st.markdown(f"**{info.display_name}**")
            st.caption(f"模板：{info.template_name}")
            st.caption(f"{info.root}")
            if info.is_compatible_mode:
                st.caption("缺少项目说明文件")
            if st.session_state.migration_notes:
                st.warning("检测到旧版配置结构")
                for note in st.session_state.migration_notes:
                    st.caption(f"· {note}")
                if st.button("保存升级后的结构", key="save_migrated_config", use_container_width=True):
                    try:
                        save_yaml(info.config_path, st.session_state.current_config)
                        st.session_state.base_config = deep_copy_config(
                            st.session_state.current_config
                        )
                        st.session_state.migration_notes = []
                        st.session_state.status_message = "配置结构已升级并保存"
                        st.rerun()
                    except Exception as exc:
                        st.session_state.last_error = f"升级保存失败：{exc}"

            tab_open2, tab_new2 = st.tabs(["打开其他", "新建"])
            with tab_open2:
                path_input2 = st.text_input(
                    "项目路径",
                    key="sidebar_open_path",
                    placeholder=r"D:\projects\other_chart",
                    label_visibility="collapsed",
                )
                if st.button("切换项目", key="sidebar_load", use_container_width=True):
                    if path_input2.strip():
                        _load_project(path_input2.strip())
                        st.rerun()
            with tab_new2:
                new_path2 = st.text_input("保存位置", key="sidebar_new_path", placeholder="D:\\projects\\new")
                if st.button("新建并切换", key="sidebar_create", use_container_width=True):
                    if new_path2.strip():
                        tpl = st.session_state.get("new_template", "line_chart_basic")
                        ok, msg, ninfo = create_project(new_path2.strip(), template_name=tpl)
                        if ok and ninfo:
                            _load_project(str(ninfo.root))
                            st.session_state.status_message = msg
                            st.rerun()
                        else:
                            st.session_state.last_error = msg

            if st.button("重新加载项目", key="reload_project", use_container_width=True):
                _load_project(str(info.root))
                st.rerun()
            if st.button("重新加载绘图核心", key="reload_core", use_container_width=True):
                try:
                    _reload_draw_chart()
                    st.session_state.status_message = "已重新加载绘图核心文件"
                    st.rerun()
                except Exception as exc:
                    st.session_state.last_error = f"重载绘图核心失败：{exc}"
            if st.button("恢复已保存配置", key="reset_config_sidebar", use_container_width=True):
                if _unsaved():
                    _reset_to_saved_config()
                    st.session_state.status_message = "已恢复为上次保存的配置"
                    st.rerun()
                else:
                    st.session_state.status_message = "当前配置与已保存版本一致"

        st.divider()

        st.radio(
            "面板模式",
            options=["简洁模式", "高级模式"],
            key="panel_mode",
            help="简洁模式按图表逻辑分组；高级模式按 YAML 结构展开",
        )

        if st.session_state.current_config:
            updated = render_config_panel(
                st.session_state.current_config,
                mode=st.session_state.panel_mode,
                widget_prefix=widget_prefix,
                template_id=info.template_id,
            )
            st.session_state.current_config = updated

_ensure_sidebar_visible_once()

# ---------------------------------------------------------------------------
# 主区域：图表预览 + 导出/保存
# ---------------------------------------------------------------------------
info = st.session_state.project_info
cfg = st.session_state.current_config

st.subheader("图表实时预览")
meta_items = []
if info and cfg:
    meta_items = [
        f"**模板** {info.template_name}",
        f"**画布** {_get_canvas_size(cfg)}",
        f"**导出 DPI** {_get_export_dpi(cfg)}",
        f"**路径** `{info.root}`",
        f"**未保存改动** {'是' if _unsaved() else '否'}",
    ]
    _, transparent = _get_export_settings(cfg)
    if transparent:
        meta_items.append("**透明背景** 开")

if meta_items:
    st.markdown(" · ".join(meta_items))

preview_placeholder = st.container(border=True)
with preview_placeholder:
    if cfg and st.session_state.draw_chart_fn:
        fig = _render_chart(cfg)
        if fig is not None:
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
            if st.session_state.get("font_fallback_warning"):
                st.warning(st.session_state.font_fallback_warning)
            st.success("最近一次渲染：成功")
        else:
            st.error(st.session_state.render_error or "图表渲染失败")
            if st.session_state.render_trace:
                with st.expander("查看错误详情"):
                    st.code(st.session_state.render_trace)
            st.markdown(
                """
                **排查建议：**
                - 检查「绘图核心文件」是否包含正确的绘图函数
                - 确认「图表配置文件」中的数据格式正确
                - 可切换到 Sidebar「高级模式」查看完整配置
                """,
            )
    elif not info:
        st.markdown(
            """
            <div class="cs-preview-box" style="text-align:center;padding:80px 20px;color:#888;">
            请在左侧 Sidebar 打开或新建项目，图表将在此处实时预览
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="cs-preview-box" style="text-align:center;padding:80px 20px;color:#888;">
            加载项目中…
            </div>
            """,
            unsafe_allow_html=True,
        )

if info and cfg:
    st.markdown("##### 导出与保存")
    output_dir = info.root / "output"
    st.caption(f"导出目录：`{output_dir}` · 透明背景对 PNG/SVG 效果最佳")

    e1, e2, e3, e4 = st.columns(4)
    dpi_int, transparent = _get_export_settings(cfg)

    with e1:
        if st.button("导出 PNG", use_container_width=True, type="primary"):
            export_fig = _render_chart(cfg)
            if export_fig is None:
                st.error("无法导出：请先修复图表渲染错误")
            else:
                try:
                    path = export_figure(
                        export_fig, output_dir, "png", dpi=dpi_int, transparent=transparent
                    )
                    st.session_state.status_message = f"已导出 PNG：{path.name}"
                    plt.close(export_fig)
                    st.rerun()
                except Exception as exc:
                    st.error(f"PNG 导出失败：{exc}")
                    plt.close(export_fig)

    with e2:
        if st.button("导出 SVG", use_container_width=True):
            export_fig = _render_chart(cfg)
            if export_fig is None:
                st.error("无法导出：请先修复图表渲染错误")
            else:
                try:
                    path = export_figure(
                        export_fig, output_dir, "svg", transparent=transparent
                    )
                    st.session_state.status_message = f"已导出 SVG：{path.name}"
                    plt.close(export_fig)
                    st.rerun()
                except Exception as exc:
                    st.error(f"SVG 导出失败：{exc}")
                    plt.close(export_fig)

    with e3:
        if st.button("导出 PDF", use_container_width=True):
            export_fig = _render_chart(cfg)
            if export_fig is None:
                st.error("无法导出：请先修复图表渲染错误")
            else:
                try:
                    path = export_figure(
                        export_fig, output_dir, "pdf", transparent=transparent
                    )
                    st.session_state.status_message = f"已导出 PDF：{path.name}"
                    plt.close(export_fig)
                    st.rerun()
                except Exception as exc:
                    st.error(f"PDF 导出失败：{exc}")
                    plt.close(export_fig)

    with e4:
        if st.button("打开输出目录", use_container_width=True):
            output_dir.mkdir(parents=True, exist_ok=True)
            try:
                import os
                os.startfile(str(output_dir))  # noqa: S606 — Windows only
            except Exception:
                st.info(f"请手动打开文件夹：\n{output_dir}")

    s1, s2, s3 = st.columns(3)
    with s1:
        if st.button("保存当前配置", use_container_width=True, type="primary"):
            try:
                save_yaml(info.config_path, st.session_state.current_config)
                st.session_state.base_config = deep_copy_config(st.session_state.current_config)
                st.session_state.migration_notes = []
                st.session_state.status_message = "配置已保存到图表配置文件"
                st.rerun()
            except Exception as exc:
                st.session_state.last_error = f"保存失败：{exc}"
                st.session_state.last_error_trace = traceback.format_exc()
    with s2:
        if st.button("另存配置快照", use_container_width=True):
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
    with s3:
        if st.button("恢复已保存配置", use_container_width=True):
            if _unsaved():
                _reset_to_saved_config()
                st.session_state.status_message = "已恢复为上次保存的配置"
                st.rerun()
            else:
                st.session_state.status_message = "当前配置与已保存版本一致"

# ---------------------------------------------------------------------------
# 底部折叠区
# ---------------------------------------------------------------------------
st.divider()

with st.expander("当前改动记录", expanded=bool(_unsaved())):
    if st.session_state.base_config and st.session_state.current_config:
        changes = compare_configs(
            st.session_state.base_config,
            st.session_state.current_config,
            human_readable=True,
        )
        if changes:
            for line in changes:
                st.markdown(f"- {line}")
        else:
            st.caption("暂无改动，与上次保存的配置一致。")
    else:
        st.caption("打开项目后可查看参数改动。")

with st.expander("查看图表配置文件（YAML 原文）"):
    if st.session_state.current_config:
        st.code(
            yaml.dump(
                strip_internal_keys(st.session_state.current_config),
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            ),
            language="yaml",
        )
    else:
        st.caption("打开项目后可查看完整配置。")

with st.expander("让 AI 生成兼容 ChartStudio 的代码"):
    st.markdown(
        "复制下方提示词到 ChatGPT / Claude 等 AI 工具，"
        "可生成可直接导入 ChartStudio 的图表项目文件。"
    )
    st.code(get_ai_prompt(), language="text")
    st.download_button(
        "下载提示词文本",
        data=get_ai_prompt(),
        file_name="chartstudio_ai_prompt.txt",
        mime="text/plain",
        use_container_width=True,
    )
