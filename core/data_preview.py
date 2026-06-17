"""当前 data 表格预览 — 简洁模式用表格，高级模式可用 JSON。"""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st


def data_to_preview_frame(data: dict, template_id: str) -> Optional[pd.DataFrame]:
    if not isinstance(data, dict) or not data:
        return None

    if template_id in ("line_chart_basic", "line_chart_report", "line_chart"):
        x = data.get("x", [])
        if not x:
            return None
        frame: dict[str, Any] = {"x": x}
        for key, vals in data.items():
            if key != "x":
                label = key
                frame[label] = vals
        return pd.DataFrame(frame)

    if template_id in ("bar_chart_basic", "horizontal_bar_chart"):
        cats = data.get("categories", [])
        vals = data.get("values", [])
        if not cats:
            return None
        return pd.DataFrame({"category": cats, "value": vals})

    if template_id == "scatter_chart_basic":
        rows = []
        for group, grp in data.items():
            if not isinstance(grp, dict):
                continue
            xs = grp.get("x", [])
            ys = grp.get("y", [])
            for x, y in zip(xs, ys):
                rows.append({"group": group, "x": x, "y": y})
        if not rows:
            return None
        return pd.DataFrame(rows)

    if template_id == "heatmap_basic":
        matrix = data.get("matrix", [])
        x_labels = data.get("x_labels", [])
        y_labels = data.get("y_labels", [])
        if not matrix:
            return None
        cols = [str(c) for c in x_labels] if x_labels else [f"col_{i}" for i in range(len(matrix[0]))]
        index = [str(r) for r in y_labels] if y_labels else [f"row_{i}" for i in range(len(matrix))]
        return pd.DataFrame(matrix, columns=cols, index=index)

    return None


def render_data_preview(
    data: dict,
    template_id: str,
    *,
    show_json: bool = False,
) -> None:
    st.markdown("**当前数据预览**")
    frame = data_to_preview_frame(data, template_id)
    if frame is not None:
        st.dataframe(frame, use_container_width=True)
    else:
        st.caption("暂无结构化数据可预览。")
    if show_json:
        with st.expander("JSON 原文", expanded=False):
            st.json(data)
    st.caption("上传新文件可替换当前数据。")
