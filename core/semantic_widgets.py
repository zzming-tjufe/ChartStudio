"""
语义化 Streamlit 控件 — 根据字段路径与值类型选择合适控件。
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import streamlit as st

from core.field_labels import get_field_label

_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")

# 整数 slider 范围
INT_SLIDER_RULES: Dict[str, Tuple[int, int]] = {
    "font.title_size": (8, 36),
    "font.label_size": (8, 28),
    "font.tick_size": (6, 24),
    "font.legend_size": (6, 24),
    "legend.fontsize": (6, 24),
    "data_labels.fontsize": (6, 20),
    "data_labels.decimals": (0, 6),
    "export.dpi": (72, 600),
    "chart.dpi": (72, 600),
}

# 浮点 slider 范围
FLOAT_SLIDER_RULES: Dict[str, Tuple[float, float, float]] = {
    "figure.width": (4.0, 20.0, 0.5),
    "figure.height": (3.0, 16.0, 0.5),
    "chart.width": (4.0, 20.0, 0.5),
    "chart.height": (3.0, 16.0, 0.5),
    "line_style.width": (0.5, 6.0, 0.1),
    "line_style.line_width": (0.5, 6.0, 0.1),
    "line_style.marker_size": (0.0, 20.0, 0.5),
    "line_style.marker_edge_width": (0.0, 3.0, 0.1),
    "line_style.alpha": (0.0, 1.0, 0.05),
    "axes.grid_alpha": (0.0, 1.0, 0.05),
    "bar_style.width": (0.1, 1.0, 0.05),
    "bar_style.edge_width": (0.0, 3.0, 0.1),
    "bar_style.alpha": (0.0, 1.0, 0.05),
    "scatter_style.size": (5.0, 200.0, 5.0),
    "scatter_style.alpha": (0.0, 1.0, 0.05),
    "scatter_style.edge_width": (0.0, 3.0, 0.1),
    "heatmap.linewidth": (0.0, 3.0, 0.1),
}


from core.field_options import SELECT_FIELD_OPTIONS


def _render_heatmap_cmap_field(value: str, prefix: str) -> str:
    """热力图色图 — 中文名称 + 场景说明。"""
    from core.heatmap_cmaps import (
        HEATMAP_CMAP_OPTIONS,
        cmap_display_label,
        get_cmap_option,
    )

    label = get_field_label("heatmap.cmap")
    widget_key = _widget_key("heatmap.cmap", prefix)
    ids = [o.id for o in HEATMAP_CMAP_OPTIONS]
    current = str(value or "RdYlBu_r")
    if current not in ids:
        ids = [current] + ids

    selected = st.selectbox(
        label,
        options=ids,
        index=ids.index(current),
        format_func=cmap_display_label,
        key=widget_key,
        help="发散色适合相关矩阵；顺序色适合强度/频次；灰度适合打印。",
    )
    opt = get_cmap_option(selected)
    if opt:
        st.caption(f"**{opt.group}** · {opt.hint}")
    elif selected != current:
        st.caption("当前为自定义色图名，仍由 Matplotlib 渲染。")

    with st.expander("色图选择参考", expanded=False):
        last_group = ""
        for o in HEATMAP_CMAP_OPTIONS:
            if o.group != last_group:
                st.markdown(f"**{o.group}**")
                last_group = o.group
            st.markdown(f"- **{o.label}**（`{o.id}`）：{o.hint}")

    return selected


def _render_select_field(path: str, value: str, options: List[str], prefix: str) -> str:
    label = get_field_label(path)
    widget_key = _widget_key(path, prefix)
    if value in options:
        return st.selectbox(label, options, index=options.index(value), key=widget_key)
    return st.selectbox(label, options, key=widget_key)


def is_color_string(value: Any) -> bool:
    return isinstance(value, str) and bool(_COLOR_PATTERN.match(value))


def _widget_key(path: str, prefix: str = "cfg") -> str:
    return f"{prefix}_{path.replace('.', '_')}"


def _ends_with_alpha(path: str) -> bool:
    return path.endswith("alpha") or path.endswith("_alpha")


def _get_system_fonts_dir() -> str | None:
    """返回系统字体目录（Windows / macOS / Linux 常见路径）。"""
    if os.name == "nt":
        win_fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
        if win_fonts.is_dir():
            return str(win_fonts)
    for candidate in (
        Path("/Library/Fonts"),
        Path("/System/Library/Fonts"),
        Path.home() / "Library/Fonts",
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
    ):
        if candidate.is_dir():
            return str(candidate)
    return None


def _get_project_fonts_dir() -> Path | None:
    """当前项目的 fonts/ 目录。"""
    info = st.session_state.get("project_info")
    if not info:
        return None
    fonts_dir = Path(info.root) / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)
    return fonts_dir


def _normalize_picked_font_path(picked: str) -> str:
    """
    将用户选择的字体路径写入配置。

    - 若文件在项目 fonts/ 下 → 存相对路径 fonts/xxx.ttf
    - 若在项目根目录下 → 存相对路径
    - 系统字体等其他位置 → 存绝对路径
    """
    picked_path = Path(picked).resolve()
    info = st.session_state.get("project_info")
    if info:
        root = Path(info.root).resolve()
        fonts_dir = root / "fonts"
        try:
            rel = picked_path.relative_to(fonts_dir)
            return f"fonts/{rel.as_posix()}"
        except ValueError:
            pass
        try:
            rel = picked_path.relative_to(root)
            return rel.as_posix()
        except ValueError:
            pass
    return str(picked_path)


def _build_font_filetypes() -> list[tuple[str, str]]:
    """Windows 下扩展名须用分号分隔；默认「所有文件」以免子文件夹被过滤隐藏。"""
    if os.name == "nt":
        return [
            ("所有文件", "*.*"),
            ("字体文件", "*.ttf;*.otf;*.ttc"),
            ("TrueType", "*.ttf"),
            ("OpenType", "*.otf"),
        ]
    return [
        ("所有文件", "*.*"),
        ("字体文件", "*.ttf *.otf *.ttc"),
        ("TrueType", "*.ttf"),
        ("OpenType", "*.otf"),
    ]


def _resolve_initial_font_dir(source: str) -> str:
    """根据来源解析对话框起始目录。"""
    if source == "project":
        proj_fonts = _get_project_fonts_dir()
        if proj_fonts and proj_fonts.is_dir():
            return str(proj_fonts.resolve())
    system_fonts = _get_system_fonts_dir()
    if system_fonts and Path(system_fonts).is_dir():
        return str(Path(system_fonts).resolve())
    return str(Path.home())


def pick_font_file_dialog(source: str = "system") -> str | None:
    """
    打开字体文件选择对话框。

    source="system" → 系统字体目录（如 C:\\Windows\\Fonts）
    source="project" → 当前项目的 fonts/ 目录
    """
    try:
        import tkinter as tk
        from tkinter import filedialog

        initial_dir = _resolve_initial_font_dir(source)
        titles = {
            "project": "选择项目 fonts/ 目录下的字体文件",
            "system": "选择系统字体文件",
        }

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askopenfilename(
            title=titles.get(source, titles["system"]),
            initialdir=initial_dir,
            filetypes=_build_font_filetypes(),
        )
        root.destroy()
        return path if path else None
    except Exception:
        return None


def _render_font_role_select(
    label: str,
    name_key: str,
    path_key: str,
    font_cfg: Dict[str, Any],
    catalog: Dict[str, str],
    preferred: List[str],
    prefix: str,
) -> None:
    from core.system_fonts import resolve_font_path_by_name, sort_font_names

    options = sort_font_names(catalog.keys(), preferred)
    current_name = str(font_cfg.get(name_key, preferred[0] if preferred else ""))
    if not options:
        options = list(preferred) if preferred else [current_name or "（未检测到系统字体）"]
    if current_name and current_name not in options:
        options = [current_name] + options

    widget_key = _widget_key(f"font.{name_key}", prefix)
    if widget_key in st.session_state and st.session_state[widget_key] not in options:
        st.session_state[widget_key] = options[0]

    select_kwargs: Dict[str, Any] = {
        "label": label,
        "options": options,
        "key": widget_key,
    }
    if current_name in options:
        select_kwargs["index"] = options.index(current_name)

    selected = st.selectbox(**select_kwargs)
    font_cfg[name_key] = selected
    resolved = catalog.get(selected) or resolve_font_path_by_name(selected)
    if resolved:
        font_cfg[path_key] = resolved
    path_text = str(font_cfg.get(path_key, "") or "")
    if path_text:
        st.caption(f"路径：`{path_text}`")


def render_font_settings(font_cfg: Dict[str, Any], prefix: str = "cfg") -> Dict[str, Any]:
    """字体设置面板：系统字体下拉 + 高级手动路径。"""
    from copy import deepcopy

    from core.system_fonts import (
        PREFERRED_EN,
        PREFERRED_NUM,
        PREFERRED_ZH,
        ensure_font_defaults,
        get_font_catalog,
    )

    result = deepcopy(font_cfg)
    ensure_font_defaults(result)
    catalog = get_font_catalog()

    if not catalog:
        st.info("未能读取系统字体列表，可在下方高级选项中手动填写字体路径。")

    _render_font_role_select("中文字体", "zh_name", "zh_path", result, catalog, PREFERRED_ZH, prefix)
    _render_font_role_select("英文字体", "en_name", "en_path", result, catalog, PREFERRED_EN, prefix)
    _render_font_role_select("数字字体", "num_name", "num_path", result, catalog, PREFERRED_NUM, prefix)

    for size_key in ("title_size", "label_size", "tick_size", "legend_size"):
        if size_key in result:
            result[size_key] = render_field_widget(
                f"font.{size_key}", result[size_key], prefix=prefix
            )

    with st.expander("高级：手动指定字体文件", expanded=False):
        st.caption("留空则使用上方下拉框；填写后将覆盖对应中文字体路径")
        sync_key = _widget_key("font.file_path_sync", prefix)
        file_path_val = str(result.get("file_path", "") or "")
        if sync_key in st.session_state:
            file_path_val = st.session_state.pop(sync_key)

        result["file_path"] = st.text_input(
            "中文字体文件覆盖（font.file_path）",
            value=file_path_val,
            key=_widget_key("font.file_path", prefix),
        )
        if st.button(
            "从项目 fonts/ 选择文件",
            key=_widget_key("font.file_path_browse", prefix),
            use_container_width=True,
        ):
            picked = pick_font_file_dialog(source="project")
            if picked:
                st.session_state[sync_key] = _normalize_picked_font_path(picked)
                st.rerun()

        st.caption("当前生效路径（只读，由下拉框自动解析）")
        for path_key, path_label in (
            ("zh_path", "中文字体"),
            ("en_path", "英文字体"),
            ("num_path", "数字字体"),
        ):
            st.text(f"{path_label}：{result.get(path_key, '') or '—'}")

    return result


def render_xy_pair(path: str, value: List[Any], prefix: str = "cfg") -> List[float]:
    """渲染 [x, y] 坐标对控件。"""
    label = get_field_label(path)
    st.caption(label)
    c1, c2 = st.columns(2)
    x_val = float(value[0]) if len(value) > 0 else 0.0
    y_val = float(value[1]) if len(value) > 1 else 0.0
    with c1:
        new_x = st.number_input(
            "X",
            value=x_val,
            step=0.01,
            format="%.3f",
            key=_widget_key(f"{path}_x", prefix),
        )
    with c2:
        new_y = st.number_input(
            "Y",
            value=y_val,
            step=0.01,
            format="%.3f",
            key=_widget_key(f"{path}_y", prefix),
        )
    return [float(new_x), float(new_y)]


def render_field_widget(
    path: str,
    value: Any,
    prefix: str = "cfg",
    show_path_hint: bool = False,
) -> Any:
    """
    根据字段语义渲染单个控件并返回新值。
    """
    label = get_field_label(path)
    if show_path_hint:
        label = f"{label}  (`{path}`)"

    # XY 坐标对
    if isinstance(value, list) and len(value) == 2 and all(
        isinstance(v, (int, float)) and not isinstance(v, bool) for v in value
    ):
        if path.endswith("_xy") or path.endswith("_offset") or "xy" in path.split(".")[-1]:
            return render_xy_pair(path, value, prefix)

    if isinstance(value, bool):
        return st.checkbox(label, value=value, key=_widget_key(path, prefix))

    if isinstance(value, int) and not isinstance(value, bool):
        if path in INT_SLIDER_RULES:
            lo, hi = INT_SLIDER_RULES[path]
            return st.slider(
                label,
                min_value=lo,
                max_value=hi,
                value=int(max(lo, min(hi, value))),
                step=1,
                key=_widget_key(path, prefix),
            )
        return st.number_input(
            label, value=int(value), step=1, key=_widget_key(path, prefix)
        )

    if isinstance(value, float):
        if path in FLOAT_SLIDER_RULES:
            lo, hi, step = FLOAT_SLIDER_RULES[path]
            return st.slider(
                label,
                min_value=lo,
                max_value=hi,
                value=float(max(lo, min(hi, value))),
                step=step,
                key=_widget_key(path, prefix),
            )
        if _ends_with_alpha(path) and 0.0 <= value <= 1.0:
            return st.slider(
                label,
                min_value=0.0,
                max_value=1.0,
                value=float(value),
                step=0.05,
                key=_widget_key(path, prefix),
            )
        return st.number_input(
            label,
            value=float(value),
            step=0.1,
            format="%.4f",
            key=_widget_key(path, prefix),
        )

    if is_color_string(value):
        picked = st.color_picker(label, value=value, key=_widget_key(path, prefix))
        return picked.upper() if isinstance(picked, str) and picked.startswith("#") else picked

    if isinstance(value, str):
        if path == "heatmap.cmap":
            return _render_heatmap_cmap_field(value, prefix)
        if path in SELECT_FIELD_OPTIONS:
            return _render_select_field(path, value, SELECT_FIELD_OPTIONS[path], prefix)
        if path.endswith("file_path") or path.endswith("font_path"):
            sync_key = _widget_key(f"{path}_file_sync", prefix)
            if sync_key in st.session_state:
                value = st.session_state.pop(sync_key)
            st.caption("手动字体路径；也可在「字体设置」分组中使用下拉框选择系统字体。")
            c1, c2 = st.columns([4, 1])
            with c1:
                text_val = st.text_input(label, value=value, key=_widget_key(path, prefix))
            with c2:
                st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
                if st.button(
                    "项目",
                    key=_widget_key(f"{path}_browse_proj", prefix),
                    use_container_width=True,
                    help="从当前项目 fonts/ 目录选择",
                ):
                    picked = pick_font_file_dialog(source="project")
                    if picked:
                        st.session_state[sync_key] = _normalize_picked_font_path(picked)
                        st.rerun()
            return text_val
        return st.text_input(label, value=value, key=_widget_key(path, prefix))

    if isinstance(value, list) and all(
        isinstance(v, (int, float)) and not isinstance(v, bool) for v in value
    ):
        return _render_numeric_list(path, value, prefix)

    return value


def _render_numeric_list(
    path: str, values: List[Union[int, float]], prefix: str
) -> List[Union[int, float]]:
    label = get_field_label(path)
    st.markdown(f"**{label}**")
    cols = st.columns(min(len(values), 5))
    result: List[Union[int, float]] = []
    is_int = all(isinstance(v, int) and not isinstance(v, bool) for v in values)
    for i, val in enumerate(values):
        with cols[i % len(cols)]:
            if is_int:
                new_val = st.number_input(
                    f"[{i}]",
                    value=int(val),
                    step=1,
                    key=_widget_key(f"{path}_{i}", prefix),
                    label_visibility="collapsed",
                )
                result.append(int(new_val))
            else:
                new_val = st.number_input(
                    f"[{i}]",
                    value=float(val),
                    step=0.1,
                    format="%.4f",
                    key=_widget_key(f"{path}_{i}", prefix),
                    label_visibility="collapsed",
                )
                result.append(float(new_val))
    return result


def render_canvas_size(path_w: str, path_h: str, config: dict, prefix: str = "cfg"):
    """画布宽高 — 仅使用 number_input，避免 slider 与输入框不同步。"""
    from core.config_utils import get_by_path, set_by_path, _MISSING

    w_val = get_by_path(config, path_w)
    h_val = get_by_path(config, path_h)

    if w_val is _MISSING or h_val is _MISSING:
        return config

    st.caption("画布尺寸（英寸）")
    c1, c2 = st.columns(2)
    with c1:
        w_num = st.number_input(
            get_field_label(path_w),
            min_value=4.0,
            max_value=24.0,
            value=float(w_val),
            step=0.1,
            format="%.1f",
            key=_widget_key(path_w, prefix),
        )
        set_by_path(config, path_w, float(w_num))
    with c2:
        h_num = st.number_input(
            get_field_label(path_h),
            min_value=3.0,
            max_value=20.0,
            value=float(h_val),
            step=0.1,
            format="%.1f",
            key=_widget_key(path_h, prefix),
        )
        set_by_path(config, path_h, float(h_num))
    return config
