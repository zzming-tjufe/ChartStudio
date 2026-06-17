"""
项目路径输入 — 文本 / 浏览 / 拖入配置文件，带状态反馈。
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Literal, Optional, Tuple

import streamlit as st
import yaml

PROJECT_MARKER_NAMES = frozenset(
    {"chart_config.yaml", "chart_project.yaml", "chart_core.py"}
)

PathStatus = Literal["idle", "ready", "warn", "error", "validating", "valid_drop"]


def _pick_folder_dialog(title: str = "选择文件夹") -> Optional[str]:
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


def _pick_config_file_dialog(title: str = "选择项目配置文件") -> Optional[str]:
    """选择 chart_config.yaml 等，返回文件完整路径。"""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        file_path = filedialog.askopenfilename(
            title=title,
            filetypes=[
                ("ChartStudio 项目文件", "chart_config.yaml chart_project.yaml chart_core.py"),
                ("YAML 配置", "*.yaml *.yml"),
                ("Python 绘图核心", "*.py"),
                ("所有文件", "*.*"),
            ],
        )
        root.destroy()
        return file_path if file_path else None
    except Exception:
        return None


def _project_root_from_file(file_path: str) -> str:
    return str(Path(file_path).expanduser().resolve().parent)


def validate_dropped_project_file(filename: str, raw: bytes) -> Tuple[bool, str]:
    """校验拖入的项目标记文件。"""
    name = filename.lower()
    if name not in PROJECT_MARKER_NAMES:
        return (
            False,
            f"请拖入 chart_config.yaml、chart_project.yaml 或 chart_core.py（当前：{filename}）",
        )
    if name.endswith((".yaml", ".yml")):
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                text = raw.decode("gbk")
            except UnicodeDecodeError:
                return False, "无法读取 YAML 文件编码"
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            return False, f"YAML 格式无效：{exc}"
        if not isinstance(data, dict):
            return False, "配置文件内容不是有效的键值结构"
        return True, f"已识别有效的配置文件「{filename}」"
    if name == "chart_core.py":
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            return False, "无法读取 chart_core.py"
        if "def draw_chart" not in text:
            return False, "该 Python 文件不包含 draw_chart 函数，可能不是 ChartStudio 绘图核心"
        return True, f"已识别有效的绘图核心「{filename}」"
    return False, "不支持的文件类型"


def assess_new_project_path(path: str) -> Tuple[PathStatus, str]:
    """评估新建项目目标路径是否可用。"""
    text = path.strip()
    if not text:
        return "idle", "请输入或浏览选择保存位置"
    try:
        root = Path(text).expanduser().resolve()
    except (OSError, ValueError):
        return "error", "路径格式无效，请检查输入"
    if root.exists() and any(root.iterdir()):
        return "warn", f"文件夹非空：{root}"
    if root.exists():
        return "ready", f"文件夹为空，可在此创建项目：{root}"
    parent = root.parent
    if not parent.exists():
        return "warn", f"上级目录不存在，创建时将尝试新建：{root}"
    return "ready", f"将创建新项目文件夹：{root}"


def assess_open_project_path(path: str) -> Tuple[PathStatus, str]:
    """评估打开项目路径（不加载项目，仅提示）。"""
    text = path.strip()
    if not text:
        return "idle", "输入路径、浏览文件夹，或拖入项目配置文件"
    try:
        root = Path(text).expanduser().resolve()
    except (OSError, ValueError):
        return "error", "路径格式无效"
    if not root.is_dir():
        return "error", f"找不到文件夹：{root}"
    config = root / "chart_config.yaml"
    core = root / "chart_core.py"
    missing = []
    if not config.is_file():
        missing.append("chart_config.yaml")
    if not core.is_file():
        missing.append("chart_core.py")
    if missing:
        return "error", f"缺少必需文件：{', '.join(missing)}"
    return "ready", f"检测到有效 ChartStudio 项目：{root.name}"


def _render_status_badge(status: PathStatus, message: str) -> None:
    if status == "idle" or not message:
        return
    styles = {
        "ready": ("cs-path-ok", "✅"),
        "valid_drop": ("cs-path-ok", "✅"),
        "warn": ("cs-path-warn", "⚠️"),
        "error": ("cs-path-error", "❌"),
        "validating": ("cs-path-warn", "⏳"),
    }
    css_class, icon = styles.get(status, ("cs-path-warn", "·"))
    st.markdown(
        f'<div class="{css_class}">{icon} {message}</div>',
        unsafe_allow_html=True,
    )


def render_open_project_path_input(
    *,
    path_key: str = "open_path_input",
    upload_key: str = "open_project_drop",
    browse_key: str = "browse_open",
    locate_key: str = "locate_open",
    open_key: str = "load_project",
    on_queue_path: Callable[[str], None],
    on_open: Callable[[str], None],
    compact: bool = False,
) -> None:
    """打开项目：路径输入 + 文件夹浏览 + 拖入配置文件 + 状态反馈。"""
    drop_status_key = f"{upload_key}_status"
    drop_msg_key = f"{upload_key}_msg"

    if drop_status_key not in st.session_state:
        st.session_state[drop_status_key] = "idle"
        st.session_state[drop_msg_key] = ""

    if not compact:
        st.markdown("**打开已有项目**")
        st.caption("输入文件夹路径、点击浏览，或将 chart_config.yaml 拖入下方区域")

    uploaded = st.file_uploader(
        "拖入项目配置文件",
        type=["yaml", "yml", "py"],
        key=upload_key,
        label_visibility="collapsed" if compact else "visible",
        help="支持 chart_config.yaml、chart_project.yaml、chart_core.py",
    )

    if uploaded is not None:
        ok, msg = validate_dropped_project_file(uploaded.name, uploaded.getvalue())
        st.session_state[drop_status_key] = "valid_drop" if ok else "error"
        st.session_state[drop_msg_key] = msg
        if ok:
            st.session_state[f"{upload_key}_marker"] = uploaded.name

    drop_status = st.session_state.get(drop_status_key, "idle")
    drop_msg = st.session_state.get(drop_msg_key, "")
    if drop_status == "valid_drop" and drop_msg:
        _render_status_badge("valid_drop", drop_msg)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("定位文件夹并填入路径", key=locate_key, use_container_width=True):
                marker = st.session_state.get(f"{upload_key}_marker", "chart_config.yaml")
                picked = _pick_config_file_dialog(f"选择刚才拖入的 {marker}")
                if picked:
                    on_queue_path(_project_root_from_file(picked))
                    st.session_state[drop_status_key] = "ready"
                    st.session_state[drop_msg_key] = f"已定位项目文件夹：{_project_root_from_file(picked)}"
                    st.rerun()
        with c2:
            if st.button("定位并打开", key=f"{open_key}_drop", type="primary", use_container_width=True):
                marker = st.session_state.get(f"{upload_key}_marker", "chart_config.yaml")
                picked = _pick_config_file_dialog(f"选择刚才拖入的 {marker}")
                if picked:
                    on_open(_project_root_from_file(picked))
                    st.rerun()

    path_input = st.text_input(
        "项目文件夹",
        placeholder=r"D:\projects\my_chart",
        key=path_key,
        label_visibility="collapsed" if compact else "visible",
    )

    path_status, path_msg = assess_open_project_path(path_input)
    if path_status != "idle":
        _render_status_badge(path_status, path_msg)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("浏览文件夹", key=browse_key, use_container_width=True):
            picked = _pick_folder_dialog("选择 ChartStudio 项目文件夹")
            if picked:
                on_queue_path(picked)
                st.rerun()
    with c2:
        if st.button("选择配置文件", key=f"{browse_key}_file", use_container_width=True):
            picked = _pick_config_file_dialog("选择 chart_config.yaml 以定位项目")
            if picked:
                on_queue_path(_project_root_from_file(picked))
                st.rerun()
    with c3:
        if st.button("打开项目", key=open_key, type="primary", use_container_width=True):
            if path_input.strip():
                on_open(path_input.strip())
                st.rerun()
            else:
                st.session_state.last_error = "请先输入、浏览或拖入配置文件以定位项目文件夹"


def render_new_project_path_input(
    *,
    path_key: str = "new_path_input",
    browse_key: str = "browse_new",
    create_key: str = "create_project",
    on_queue_path: Callable[[str], None],
    compact: bool = False,
) -> Tuple[str, PathStatus, str]:
    """新建项目路径输入，返回 (path, status, message)。"""
    if not compact:
        st.markdown("**新建项目保存位置**")
        st.caption("选择空文件夹，或输入尚未存在的路径")

    new_path = st.text_input(
        "保存位置",
        placeholder=r"D:\projects\new_chart",
        key=path_key,
        label_visibility="collapsed" if compact else "visible",
    )

    status, msg = assess_new_project_path(new_path)
    _render_status_badge(status, msg)

    if st.button("浏览文件夹", key=browse_key, use_container_width=True):
        picked = _pick_folder_dialog("选择新建项目的目标文件夹")
        if picked:
            on_queue_path(picked)
            st.rerun()

    return new_path, status, msg
