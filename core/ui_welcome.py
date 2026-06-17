"""
欢迎态界面 — 无项目时的主区域与侧栏。
"""

from __future__ import annotations

from typing import Callable

import streamlit as st

from core.project_path_input import render_new_project_path_input, render_open_project_path_input
from core.template_gallery import render_template_gallery


def render_welcome_sidebar(
    *,
    on_queue_open_path: Callable[[str], None],
    on_queue_new_path: Callable[[str], None],
    on_open: Callable[[str], None],
    on_create: Callable[[str, str, str | None], None],
) -> None:
    st.markdown("### 开始")
    st.caption("创建新项目，或打开已有项目")

    tab_open, tab_new = st.tabs(["打开项目", "新建项目"])

    with tab_open:
        render_open_project_path_input(
            path_key="sidebar_open_path_input",
            upload_key="sidebar_open_drop",
            browse_key="sidebar_browse_open",
            locate_key="sidebar_locate_open",
            open_key="sidebar_load_project",
            on_queue_path=on_queue_open_path,
            on_open=on_open,
            compact=True,
        )

    with tab_new:
        st.caption("请在主区域选择图表模板。")
        template_name = st.session_state.get("new_template", "line_chart_basic")
        new_path, _, _ = render_new_project_path_input(
            path_key="sidebar_new_path_input",
            browse_key="sidebar_browse_new",
            on_queue_path=on_queue_new_path,
            compact=True,
        )
        project_name = st.text_input("项目名称（可选）", key="new_project_name")
        if st.button(
            "创建项目",
            key="create_project",
            type="primary",
            use_container_width=True,
        ):
            if new_path.strip():
                on_create(new_path.strip(), template_name, project_name or None)
            else:
                st.session_state.last_error = "请先输入新建项目的保存位置"


def render_welcome_main(
    *,
    on_queue_open_path: Callable[[str], None],
    on_queue_new_path: Callable[[str], None],
    on_open: Callable[[str], None],
    on_create: Callable[[str, str, str | None], None],
) -> None:
    st.markdown("## 开始制作图表")
    st.markdown(
        "选择模板创建新项目，或打开已有项目。进入编辑界面后可导入数据、调整样式并导出。"
    )

    col_open, col_new = st.columns(2, gap="large")

    with col_open:
        with st.container(border=True):
            render_open_project_path_input(
                path_key="main_open_path_input",
                upload_key="main_open_drop",
                browse_key="main_browse_open",
                locate_key="main_locate_open",
                open_key="main_load_project",
                on_queue_path=on_queue_open_path,
                on_open=on_open,
            )

    with col_new:
        with st.container(border=True):
            st.markdown("**新建项目**")
            st.caption("选择图表模板与保存位置")
            render_template_gallery(key_prefix="main_gallery")
            template_name = st.session_state.get("new_template", "line_chart_basic")
            new_path, status, _ = render_new_project_path_input(
                path_key="main_new_path_input",
                browse_key="main_browse_new",
                on_queue_path=on_queue_new_path,
            )
            project_name = st.text_input("项目名称（可选）", key="new_project_name_main")
            if st.button("创建项目", key="create_project_main", type="primary", use_container_width=True):
                if new_path.strip():
                    on_create(new_path.strip(), template_name, project_name or None)
                else:
                    st.session_state.last_error = "请先输入新建项目的保存位置"
            elif status == "warn":
                st.caption("目标文件夹非空时无法创建，请换一个空文件夹。")

    st.markdown("---")
    st.caption(f"当前选中模板：{st.session_state.get('new_template', 'line_chart_basic')}")
