"""
欢迎态界面 — 无项目时的主区域与侧栏。
"""

from __future__ import annotations

from typing import Callable

import streamlit as st

from core.path_utils import sanitize_project_name
from core.project_path_input import render_new_project_path_input, render_open_project_path_input
from core.template_gallery import render_template_gallery


def _validate_create_inputs(parent_path: str, project_name: str) -> str | None:
    """返回错误信息，通过则返回 None。"""
    if not parent_path.strip():
        return "请先选择或输入保存目录"
    if not sanitize_project_name(project_name):
        return "请输入有效的项目名称"
    return None


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
        new_path, project_name, _, _ = render_new_project_path_input(
            path_key="sidebar_new_path_input",
            project_name_key="new_project_name",
            browse_key="sidebar_browse_new",
            on_queue_path=on_queue_new_path,
            compact=True,
        )
        if st.button(
            "创建项目",
            key="create_project",
            type="primary",
            use_container_width=True,
        ):
            err = _validate_create_inputs(new_path, project_name)
            if err:
                st.session_state.last_error = err
            else:
                on_create(new_path.strip(), template_name, project_name.strip())


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
            st.caption("选择模板，填写项目名与保存目录")
            render_template_gallery(key_prefix="main_gallery")
            template_name = st.session_state.get("new_template", "line_chart_basic")
            new_path, project_name, status, _ = render_new_project_path_input(
                path_key="main_new_path_input",
                project_name_key="new_project_name_main",
                browse_key="main_browse_new",
                on_queue_path=on_queue_new_path,
            )
            if st.button("创建项目", key="create_project_main", type="primary", use_container_width=True):
                err = _validate_create_inputs(new_path, project_name)
                if err:
                    st.session_state.last_error = err
                else:
                    on_create(new_path.strip(), template_name, project_name.strip())
            elif status == "warn":
                st.caption("请填写项目名称，并确保目标子文件夹不存在或为空。")

    st.markdown("---")
    st.caption(f"当前选中模板：{st.session_state.get('new_template', 'line_chart_basic')}")
