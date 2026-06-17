"""
调参面板工厂 — 支持简洁模式（图表逻辑分组）与高级模式（YAML 结构展开）。
"""

from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from core.config_loader import INTERNAL_CONFIG_KEYS, deep_copy_config
from core.field_labels import get_field_label
from core.panel_groups import render_simple_panel
from core.semantic_widgets import render_field_widget, render_font_settings


def _is_numeric_list(value: Any) -> bool:
    if not isinstance(value, list) or len(value) == 0:
        return False
    return all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value)


def _render_advanced_recursive(
    config: Dict[str, Any],
    path: str = "",
    prefix: str = "adv",
) -> Dict[str, Any]:
    """高级模式：按 YAML 结构递归展开，控件使用语义化渲染。"""
    result: Dict[str, Any] = {}

    for key, value in config.items():
        if key in INTERNAL_CONFIG_KEYS or str(key).startswith("_"):
            result[key] = value
            continue

        full_path = f"{path}.{key}" if path else key

        if key == "data" and isinstance(value, dict):
            from core.data_importer import render_data_panel

            title = get_field_label(full_path)
            with st.expander(f"{title}  (`{full_path}`)", expanded=True):
                root = None
                tpl = ""
                if st.session_state.get("project_info"):
                    root = st.session_state.project_info.root
                    tpl = st.session_state.project_info.template_id
                working = deep_copy_config({**config, **result})
                updated = render_data_panel(
                    working,
                    tpl,
                    prefix=f"{prefix}_data_adv",
                    project_root=root,
                    show_json=True,
                )
                for uk, uv in updated.items():
                    result[uk] = uv
            continue

        if key == "font" and isinstance(value, dict):
            title = get_field_label(full_path)
            with st.expander(
                f"{title}  (`{full_path}`)",
                expanded=full_path in ("chart", "font", "axes"),
            ):
                result[key] = render_font_settings(value, prefix=prefix)
            continue

        if isinstance(value, dict):
            title = get_field_label(full_path) if full_path in ("chart", "font") else key
            with st.expander(f"{title}  (`{full_path}`)", expanded=full_path in ("chart", "font", "axes")):
                result[key] = _render_advanced_recursive(value, full_path, prefix)
            continue

        new_val = render_field_widget(full_path, value, prefix=prefix, show_path_hint=True)
        result[key] = new_val

    return result


def render_config_panel(
    config: Dict[str, Any],
    mode: str = "简洁模式",
    widget_prefix: str = "cfg",
    template_id: str = "",
) -> Dict[str, Any]:
    """
    渲染调参面板。

    mode: "简洁模式" | "高级模式"
    widget_prefix: 控件 key 前缀（含项目 hash，避免切换项目污染）
    template_id: 模板 ID，用于简洁模式分组白名单
    """
    simple_prefix = f"{widget_prefix}_simple"
    adv_prefix = f"{widget_prefix}_adv"

    if mode == "高级模式":
        st.caption("高级模式：按配置文件原始结构展开，适合开发者微调。")
        return _render_advanced_recursive(config, prefix=adv_prefix)

    return render_simple_panel(
        config,
        prefix=simple_prefix,
        template_id=template_id or None,
        project_root=(
            st.session_state.project_info.root
            if st.session_state.get("project_info")
            else None
        ),
    )
