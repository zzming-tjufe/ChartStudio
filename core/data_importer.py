"""
数据导入 — CSV / Excel 上传、列映射、写入 config.data。
"""

from __future__ import annotations

import hashlib
import io
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

from core.config_utils import set_by_path
from core.data_coercion import coerce_numeric_column
from core.data_preview import render_data_preview
from core.series_sync import (
    assign_group_keys,
    assign_line_keys,
    rebuild_series_config,
)
from core.template_registry import get_template_kind


def read_uploaded_file(uploaded) -> Optional[pd.DataFrame]:
    if uploaded is None:
        return None
    name = uploaded.name.lower()
    raw = uploaded.getvalue()
    try:
        if name.endswith('.csv'):
            for enc in ("utf-8-sig", "utf-8", "gbk", "gb18030"):
                try:
                    return pd.read_csv(io.BytesIO(raw),encoding=enc)
                except UnicodeDecodeError:
                    continue
            return pd.read_csv(io.BytesIO(raw))
        if name.endswith( (".xlsx", ".xls")):
            return pd.read_excel(io.BytesIO(raw))
    except Exception as exc:
        st.error(f"文件读取失败：{exc}")
        return None
    st.error("仅支持 CSV / Excel（.xlsx / .xls）")
    return None


def save_dataframe_to_project(project_root: Path, df: pd.DataFrame, filename: str) -> Path:
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_data_filename(filename)
    out = data_dir / safe_name
    if safe_name.lower().endswith(".csv"):
        df.to_csv(out, index=False,encoding="utf-8-sig")
    else:
        df.to_excel(out, index=False)
    return out


def sanitize_data_filename(filename: str) -> str:
    name = Path(filename or "imported_data.csv").name
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", Path(name).stem).strip(" ._")
    suffix = Path(name).suffix.lower()
    if suffix == ".xls":
        suffix = ".xlsx"
    if suffix not in (".csv", ".xlsx"):
        suffix = ".csv"
    return f"{stem or 'imported_data'}{suffix}"


def _relative_to_project(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def build_line_data(
    df: pd.DataFrame, x_col: str, y_cols: List[str]
) -> Tuple[dict, Dict[str, str], List[str]]:
    data: dict = {"x": df[x_col].tolist()}
    col_to_key, key_to_label = assign_line_keys(y_cols)
    warnings: List[str] = []
    for col in y_cols:
        key = col_to_key[col]
        bundle = coerce_numeric_column(df[col], column_name=col)
        data[key] = bundle.values
        warnings.extend(bundle.warnings())
    return data, key_to_label, warnings


def build_bar_data(
    df: pd.DataFrame, cat_col: str, val_col: str
) -> Tuple[dict, Dict[str, str], List[str]]:
    bundle = coerce_numeric_column(df[val_col], column_name=val_col)
    data = {
        "categories": df[cat_col].astype(str).tolist(),
        "values": bundle.values,
    }
    return data, {}, bundle.warnings()


def build_scatter_data(
    df: pd.DataFrame, x_col: str, y_col: str, group_col: Optional[str]
) -> Tuple[dict, Dict[str, str], List[str]]:
    data: dict = {}
    key_to_label: Dict[str, str] = {}
    warnings: List[str] = []

    if group_col and group_col in df.columns:
        groups = list(df[group_col].unique())
        name_to_key, key_to_label = assign_group_keys(groups)
        for g, sub in df.groupby(group_col):
            key = name_to_key[g]
            bx = coerce_numeric_column(sub[x_col], column_name=x_col)
            by = coerce_numeric_column(sub[y_col], column_name=y_col)
            data[key] = {"x": bx.values, "y": by.values}
            warnings.extend(bx.warnings())
            warnings.extend(by.warnings())
    else:
        bx = coerce_numeric_column(df[x_col], column_name=x_col)
        by = coerce_numeric_column(df[y_col], column_name=y_col)
        data["group_a"] = {"x": bx.values, "y": by.values}
        key_to_label["group_a"] = "全部"
        warnings.extend(bx.warnings())
        warnings.extend(by.warnings())

    return data, key_to_label, warnings


def build_heatmap_from_matrix(
    df: pd.DataFrame, row_col: str, col_cols: List[str]
) -> Tuple[dict, Dict[str, str], List[str]]:
    matrix = []
    y_labels = df[row_col].astype(str).tolist()
    x_labels = list(col_cols)
    warnings: List[str] = []
    for _, row in df.iterrows():
        row_vals = []
        for c in col_cols:
            bundle = coerce_numeric_column(pd.Series([row[c]]), column_name=c)
            warnings.extend(bundle.warnings())
            row_vals.append(float(bundle.values[0]))
        matrix.append(row_vals)
    return {"x_labels": x_labels, "y_labels": y_labels, "matrix": matrix}, {}, warnings


def build_heatmap_correlation(
    df: pd.DataFrame, numeric_cols: List[str]
) -> Tuple[dict, Dict[str, str], List[str]]:
    warnings: List[str] = []
    frames = {}
    for c in numeric_cols:
        bundle = coerce_numeric_column(df[c], column_name=c)
        frames[c] = bundle.values
        warnings.extend(bundle.warnings())
    sub = pd.DataFrame(frames).dropna()
    if sub.empty:
        return {"x_labels": [], "y_labels": [], "matrix": [[]]}, {}, ["相关矩阵：无有效数值行"]
    corr = sub.corr()
    labels = [str(c) for c in corr.columns]
    return {
        "x_labels": labels,
        "y_labels": labels,
        "matrix": corr.values.tolist(),
    }, {}, warnings


def build_data_from_mapping(
    df: pd.DataFrame,
    template_id: str,
    mapping: Dict[str, Any],
) -> Tuple[dict, Dict[str, str], List[str]]:
    kind = get_template_kind(template_id)
    if kind == "line":
        return build_line_data(df, mapping["x_col"], mapping["y_cols"])
    if kind == "bar":
        return build_bar_data(df, mapping["cat_col"], mapping["val_col"])
    if kind == "scatter":
        return build_scatter_data(
            df, mapping["x_col"], mapping["y_col"], mapping.get("group_col") or None
        )
    if kind == "heatmap":
        mode = mapping.get("mode", "correlation")
        if mode == "correlation":
            return build_heatmap_correlation(df, mapping["numeric_cols"])
        return build_heatmap_from_matrix(df, mapping["row_col"], mapping["col_cols"])
    return {}, {}, []


def _show_coercion_warnings(warnings: List[str]) -> None:
    seen = set()
    for w in warnings:
        if w in seen:
            continue
        seen.add(w)
        st.warning(w)


def _columns_schema_hash(columns: List[str]) -> str:
    payload = "|".join(sorted(str(c) for c in columns))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _build_data_source_metadata(
    df: pd.DataFrame,
    template_id: str,
    mapping: Dict[str, Any],
    *,
    upload_name: str,
    saved_path: Optional[Path],
    project_root: Optional[Path],
) -> Dict[str, Any]:
    source: Dict[str, Any] = {
        "type": "uploaded_file",
        "original_name": upload_name,
        "template_id": template_id,
        "mapping": mapping,
        "columns": [str(c) for c in df.columns],
        "schema_hash": _columns_schema_hash([str(c) for c in df.columns]),
        "row_count": int(len(df)),
    }
    if saved_path is not None and project_root is not None:
        source["path"] = _relative_to_project(saved_path, project_root)
    return source


def _mapping_state_keys(prefix: str) -> List[str]:
    return [
        f"{prefix}_x",
        f"{prefix}_ys",
        f"{prefix}_cat",
        f"{prefix}_val",
        f"{prefix}_sx",
        f"{prefix}_sy",
        f"{prefix}_sg",
        f"{prefix}_hm_mode",
        f"{prefix}_hm_corr",
        f"{prefix}_hm_row",
        f"{prefix}_hm_cols",
    ]


def _clear_upload_session(prefix: str) -> None:
    for key in (
        f"{prefix}_dataframe",
        f"{prefix}_upload_name",
        f"{prefix}_saved_data_path",
        f"{prefix}_schema_hash",
        f"{prefix}_upload",
        *_mapping_state_keys(prefix),
    ):
        st.session_state.pop(key, None)


def _sync_schema_mapping_state(prefix: str, df: pd.DataFrame) -> None:
    """列结构变化时清理旧映射控件状态。"""
    new_hash = _columns_schema_hash(list(df.columns))
    old_hash = st.session_state.get(f"{prefix}_schema_hash")
    if old_hash and old_hash != new_hash:
        for key in _mapping_state_keys(prefix):
            st.session_state.pop(key, None)
    st.session_state[f"{prefix}_schema_hash"] = new_hash


def _render_data_source_banner(prefix: str, *, using_upload: bool) -> None:
    if using_upload:
        name = st.session_state.get(f"{prefix}_upload_name", "已上传文件")
        st.info(f"当前数据来源：上传文件「{name}」")
    else:
        st.caption("当前数据来源：配置文件内置 data")


def render_data_panel(
    config: Dict[str, Any],
    template_id: str,
    prefix: str = "data",
    project_root: Optional[Path] = None,
    show_json: bool = False,
) -> Dict[str, Any]:
    """数据导入与字段映射面板。"""
    st.caption("上传 CSV / Excel，映射列名后写入图表数据。保存配置时会一并写入 YAML。")

    df_key = f"{prefix}_dataframe"

    uploaded = st.file_uploader(
        "上传数据文件",
        type=["csv", "xlsx", "xls"],
        key=f"{prefix}_upload",
    )

    if uploaded is not None:
        df_new = read_uploaded_file(uploaded)
        if df_new is not None:
            _sync_schema_mapping_state(prefix, df_new)
            st.session_state[df_key] = df_new
            st.session_state[f"{prefix}_upload_name"] = uploaded.name

    df: Optional[pd.DataFrame] = st.session_state.get(df_key)
    _render_data_source_banner(prefix, using_upload=df is not None)

    if df is not None:
        if st.button("清除已上传数据", key=f"{prefix}_clear_upload", use_container_width=True):
            _clear_upload_session(prefix)
            st.rerun()

    if df is None:
        data = config.get("data")
        if isinstance(data, dict) and data:
            render_data_preview(data, template_id, show_json=show_json)
        else:
            st.info("尚未导入数据，请上传 CSV 或 Excel。")
        return config

    st.dataframe(df.head(20), use_container_width=True)
    cols = list(df.columns)
    numeric_cols = [
        c
        for c in cols
        if pd.api.types.is_numeric_dtype(df[c])
        or pd.to_numeric(df[c], errors="coerce").notna().any()
    ]

    mapping: Dict[str, Any] = {}
    result = config

    kind = get_template_kind(template_id)

    if kind == "line":
        mapping["x_col"] = st.selectbox("X 轴列", cols, key=f"{prefix}_x")
        mapping["y_cols"] = st.multiselect(
            "Y 轴列（可多选）",
            [c for c in cols if c != mapping["x_col"]],
            default=[c for c in numeric_cols if c != mapping["x_col"]][:2],
            key=f"{prefix}_ys",
        )
    elif kind == "bar":
        mapping["cat_col"] = st.selectbox("类别列", cols, key=f"{prefix}_cat")
        val_choices = numeric_cols or cols
        mapping["val_col"] = st.selectbox(
            "数值列",
            val_choices,
            index=val_choices.index(numeric_cols[0]) if numeric_cols else 0,
            key=f"{prefix}_val",
        )
    elif kind == "scatter":
        mapping["x_col"] = st.selectbox("X 列", cols, key=f"{prefix}_sx")
        y_choices = [c for c in cols if c != mapping["x_col"]]
        mapping["y_col"] = st.selectbox("Y 列", y_choices, key=f"{prefix}_sy")
        group_opts = ["（不分组）"] + [
            c for c in cols if c not in (mapping["x_col"], mapping["y_col"])
        ]
        g = st.selectbox("分组列（可选）", group_opts, key=f"{prefix}_sg")
        mapping["group_col"] = None if g == "（不分组）" else g
    elif kind == "heatmap":
        mode = st.radio(
            "热力图数据来源",
            ["从数值列生成相关矩阵", "自定义矩阵（行标签 + 多列数值）"],
            key=f"{prefix}_hm_mode",
        )
        if mode.startswith("从数值"):
            mapping["mode"] = "correlation"
            mapping["numeric_cols"] = st.multiselect(
                "选择数值列",
                numeric_cols,
                default=numeric_cols[: min(5, len(numeric_cols))],
                key=f"{prefix}_hm_corr",
            )
        else:
            mapping["mode"] = "matrix"
            mapping["row_col"] = st.selectbox("行标签列", cols, key=f"{prefix}_hm_row")
            mapping["col_cols"] = st.multiselect(
                "矩阵数值列",
                [c for c in cols if c != mapping["row_col"]],
                key=f"{prefix}_hm_cols",
            )
    else:
        st.warning(f"模板 {template_id} 暂不支持可视化映射，请手动编辑 YAML。")
        return config

    c1, c2 = st.columns(2)
    with c1:
        apply_btn = st.button(
            "应用映射到图表", type="primary", key=f"{prefix}_apply", use_container_width=True
        )
    with c2:
        save_file_btn = st.button(
            "另存到项目 data/",
            key=f"{prefix}_save_file",
            use_container_width=True,
            disabled=project_root is None,
        )

    if save_file_btn and project_root and df is not None:
        fname = st.session_state.get(f"{prefix}_upload_name", "imported_data.csv")
        path = save_dataframe_to_project(project_root, df, fname)
        st.session_state[f"{prefix}_saved_data_path"] = str(path)
        st.success(f"已保存：{path.name}")

    if apply_btn:
        try:
            if template_id in ("line_chart_basic", "line_chart_report") and not mapping.get(
                "y_cols"
            ):
                st.error("请至少选择一个 Y 轴列。")
                return config
            if (
                template_id == "heatmap_basic"
                and mapping.get("mode") == "correlation"
                and not mapping.get("numeric_cols")
            ):
                st.error("请至少选择一个数值列。")
                return config
            new_data, labels_map, coerce_warnings = build_data_from_mapping(
                df, template_id, mapping
            )
            _show_coercion_warnings(coerce_warnings)
            saved_path = None
            upload_name = st.session_state.get(f"{prefix}_upload_name", "imported_data.csv")
            if project_root is not None:
                remembered = st.session_state.get(f"{prefix}_saved_data_path")
                saved_path = Path(remembered) if remembered else save_dataframe_to_project(
                    project_root, df, upload_name
                )
            result = set_by_path(config, "data", new_data)
            result = set_by_path(
                result,
                "data_source",
                _build_data_source_metadata(
                    df,
                    template_id,
                    mapping,
                    upload_name=upload_name,
                    saved_path=saved_path,
                    project_root=project_root,
                ),
            )
            result = rebuild_series_config(result, new_data, template_id, labels_map)
            st.success("数据已写入当前配置，记得点击「保存当前配置」。")
            render_data_preview(new_data, template_id, show_json=show_json)
        except Exception as exc:
            st.error(f"映射失败：{exc}")

    return result
