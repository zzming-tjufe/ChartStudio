"""
编辑态界面 — 已打开项目时的主区域、侧栏与底部工具区。
"""

from __future__ import annotations

import os
import traceback
from datetime import datetime
from typing import Callable

import matplotlib.pyplot as plt
import streamlit as st
import yaml

from core.ai_prompt import get_ai_prompt, get_ai_prompt_for_project, read_core_source
from core.chart_linter import render_chart_checks_panel
from core.config_loader import deep_copy_config, save_yaml, strip_internal_keys
from core.config_validator import has_blocking_errors, validate_config_for_save
from core.diff_utils import compare_configs
from core.exporter import build_export_filename, export_figure
from core.project_packager import build_project_zip
from core.project_path_input import render_open_project_path_input, render_new_project_path_input
from core.snapshot_ui import render_snapshot_manager
from core.template_gallery import render_template_gallery
from core.widget_factory import render_config_panel


_PENDING_SAVE_KEY = "pending_save_validation"


def render_editor_sidebar(
    info,
    *,
    widget_prefix: str,
    unsaved: bool,
    on_load: Callable[[str], None],
    on_create: Callable[[str, str, str | None], None],
    on_reload: Callable[[], None],
    on_reload_core: Callable[[], None],
    on_reset: Callable[[], None],
    on_save_migrated: Callable[[], None],
    on_close_project: Callable[[], None],
    on_queue_open_path: Callable[[str], None],
    on_queue_new_path: Callable[[str], None],
) -> None:
    st.markdown("### 调整图表样式")
    st.caption("左侧调参 · 右侧实时预览")

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
                on_save_migrated()

        tab_open2, tab_new2 = st.tabs(["打开其他", "新建"])
        with tab_open2:
            render_open_project_path_input(
                path_key="sidebar_open_path",
                upload_key="sidebar_switch_drop",
                browse_key="sidebar_browse_switch",
                locate_key="sidebar_locate_switch",
                open_key="sidebar_load",
                on_queue_path=on_queue_open_path,
                on_open=on_load,
                compact=True,
            )
        with tab_new2:
            render_template_gallery(key_prefix="sidebar_gallery2")
            new_path2, project_name2, _, _ = render_new_project_path_input(
                path_key="sidebar_new_path",
                project_name_key="sidebar_new_project_name",
                browse_key="sidebar_browse_new",
                on_queue_path=on_queue_new_path,
                compact=True,
            )
            if st.button("新建并切换", key="sidebar_create", use_container_width=True):
                from core.path_utils import sanitize_project_name

                if not new_path2.strip():
                    st.session_state.last_error = "请先输入保存目录"
                elif not sanitize_project_name(project_name2):
                    st.session_state.last_error = "请输入有效的项目名称"
                else:
                    tpl = st.session_state.get("new_template", "line_chart_basic")
                    on_create(new_path2.strip(), tpl, project_name2.strip())

        if st.button("重新加载项目", key="reload_project", use_container_width=True):
            on_reload()
        if st.button("关闭项目", key="close_project", use_container_width=True):
            on_close_project()
        if st.button("重新加载绘图核心", key="reload_core", use_container_width=True):
            on_reload_core()
        if st.button("恢复已保存配置", key="reset_config_sidebar", use_container_width=True):
            on_reset()

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


def render_editor_preview(
    info,
    cfg,
    *,
    unsaved: bool,
    get_canvas_size: Callable,
    get_export_dpi: Callable,
    get_export_settings: Callable,
    render_chart: Callable,
) -> None:
    st.subheader("图表实时预览")
    meta_items = [
        f"**模板** {info.template_name}",
        f"**画布** {get_canvas_size(cfg)}",
        f"**导出 DPI** {get_export_dpi(cfg)}",
        f"**路径** `{info.root}`",
        f"**未保存改动** {'是' if unsaved else '否'}",
    ]
    _, transparent = get_export_settings(cfg)
    if transparent:
        meta_items.append("**透明背景** 开")
    st.markdown(" · ".join(meta_items))

    with st.container(border=True):
        fig = render_chart(cfg)
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
                - 检查绘图核心文件是否包含正确的绘图函数
                - 确认图表配置中的数据格式正确
                - 可切换到「高级模式」查看完整配置
                """,
            )


def render_render_error_main(
    info,
    cfg,
    *,
    unsaved: bool,
    get_canvas_size: Callable,
    get_export_dpi: Callable,
    render_chart: Callable,
) -> None:
    """已弃用：渲染错误仅在预览容器内展示，保留函数以兼容旧引用。"""
    render_editor_preview(
        info,
        cfg,
        unsaved=unsaved,
        get_canvas_size=get_canvas_size,
        get_export_dpi=get_export_dpi,
        get_export_settings=lambda c: (None, False),
        render_chart=render_chart,
    )


def _export_chart(
    info,
    cfg,
    fmt: str,
    *,
    render_chart: Callable,
    get_export_settings: Callable,
) -> None:
    export_fig = render_chart(cfg)
    if export_fig is None:
        st.error("无法导出：请先修复图表渲染错误")
        return
    output_dir = info.root / "output"
    dpi_int, transparent = get_export_settings(cfg)
    try:
        filename = build_export_filename(
            cfg,
            fmt,  # type: ignore[arg-type]
            project_name=info.display_name,
            project_root_name=info.root.name,
        )
        path = export_figure(
            export_fig,
            output_dir,
            fmt,  # type: ignore[arg-type]
            filename=filename,
            dpi=dpi_int if fmt == "png" else None,
            transparent=transparent,
            config=cfg,
            project_name=info.display_name,
            project_root_name=info.root.name,
        )
        st.session_state.last_export_path = str(path)
        st.session_state.status_message = f"已导出 {fmt.upper()}：{path}"
        plt.close(export_fig)
        st.rerun()
    except Exception as exc:
        st.error(f"{fmt.upper()} 导出失败：{exc}")
        plt.close(export_fig)


def render_editor_actions(
    info,
    cfg,
    *,
    unsaved: bool,
    get_export_settings: Callable,
    render_chart: Callable,
    on_save: Callable[[], None],
    on_snapshot: Callable[[], None],
    on_reset: Callable[[], None],
    on_restore_snapshot: Callable[[dict], None],
    render_probe: Callable | None = None,
) -> None:
    st.markdown("##### 图表检查")
    with st.container(border=True):
        render_chart_checks_panel(cfg, info.template_id)

    st.markdown("##### 导出与保存")
    output_dir = info.root / "output"
    st.caption(f"导出目录：`{output_dir}` · 透明背景对 PNG/SVG 效果最佳")

    e1, e2, e3, e4 = st.columns(4)
    dpi_int, transparent = get_export_settings(cfg)

    with e1:
        if st.button("导出 PNG", use_container_width=True, type="primary"):
            _export_chart(info, cfg, "png", render_chart=render_chart, get_export_settings=get_export_settings)

    with e2:
        if st.button("导出 SVG", use_container_width=True):
            _export_chart(info, cfg, "svg", render_chart=render_chart, get_export_settings=get_export_settings)

    with e3:
        if st.button("导出 PDF", use_container_width=True):
            _export_chart(info, cfg, "pdf", render_chart=render_chart, get_export_settings=get_export_settings)

    with e4:
        if st.button("打开输出目录", use_container_width=True):
            output_dir.mkdir(parents=True, exist_ok=True)
            try:
                os.startfile(str(output_dir))  # noqa: S606 — Windows
            except Exception:
                st.info(f"请手动打开文件夹：\n{output_dir}")

    last_export = st.session_state.get("last_export_path")
    if last_export:
        st.success(f"最近导出文件：`{last_export}`")
        ex1, ex2 = st.columns(2)
        with ex1:
            if st.button("打开输出文件夹", key="open_output_after_export", use_container_width=True):
                try:
                    os.startfile(str(output_dir))  # noqa: S606
                except Exception:
                    st.info(str(output_dir))
        with ex2:
            st.text_input("复制路径", value=last_export, key="last_export_copy", disabled=True)

    with st.expander("配置快照管理", expanded=False):
        render_snapshot_manager(
            info.root,
            cfg,
            on_restore_to_session=on_restore_snapshot,
            prefix="main_snap",
        )

    pending = st.session_state.get(_PENDING_SAVE_KEY)
    if pending:
        st.error("保存前校验发现严重问题，请确认是否仍要保存：")
        for item in pending:
            st.markdown(f"- **{item['field']}**：{item['message']}")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("取消保存", key="cancel_force_save", use_container_width=True):
                st.session_state.pop(_PENDING_SAVE_KEY, None)
                st.rerun()
        with c2:
            if st.button("仍然强制保存", key="force_save", use_container_width=True):
                st.session_state.pop(_PENDING_SAVE_KEY, None)
                on_save()

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        if st.button("保存当前配置", use_container_width=True, type="primary"):
            issues = validate_config_for_save(
                cfg, info.template_id, render_probe=render_probe or render_chart
            )
            if has_blocking_errors(issues):
                st.session_state[_PENDING_SAVE_KEY] = [
                    {"level": i.level, "field": i.field, "message": i.message}
                    for i in issues
                ]
                st.rerun()
            else:
                st.session_state.pop(_PENDING_SAVE_KEY, None)
                on_save()
    with s2:
        if st.button("另存配置快照", use_container_width=True):
            on_snapshot()
    with s3:
        if st.button("恢复已保存配置", use_container_width=True):
            on_reset()
    with s4:
        if st.button("打包项目 ZIP", use_container_width=True):
            try:
                zip_path = build_project_zip(info.root)
                st.session_state.status_message = f"项目已打包：{zip_path}"
                st.rerun()
            except Exception as exc:
                st.error(f"打包失败：{exc}")


def render_editor_footer(info, *, unsaved: bool) -> None:
    st.divider()

    with st.expander("当前改动记录", expanded=bool(unsaved)):
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

    with st.expander("让 AI 修改当前图表项目", expanded=False):
        if info and st.session_state.current_config:
            st.markdown(
                "复制下方提示词到 ChatGPT / Claude 等 AI 工具，"
                "可基于**当前项目**生成修改后的配置文件与绘图核心。"
            )
            user_request = st.text_area(
                "你的修改需求",
                placeholder="例如：将折线改为虚线、增大标题字号、添加误差棒…",
                key="ai_user_request",
                height=100,
            )
            core_source = read_core_source(info.core_path)
            prompt_text = get_ai_prompt_for_project(
                st.session_state.current_config,
                info.template_id,
                info.template_name,
                core_source,
                project_name=info.display_name,
                user_request=user_request,
            )
            st.code(prompt_text, language="text")
            st.download_button(
                "下载提示词文本",
                data=prompt_text,
                file_name="chartstudio_ai_modify_prompt.txt",
                mime="text/plain",
                use_container_width=True,
            )
        else:
            st.caption("请先打开项目。")
