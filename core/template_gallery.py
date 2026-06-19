"""
模板画廊 — 新建项目时的卡片式模板选择。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import streamlit as st

from core.project_manager import TEMPLATES_DIR, get_templates

APP_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class TemplateMeta:
    id: str
    name: str
    scenario: str
    description: str
    preview_path: Optional[Path] = None


TEMPLATE_CATALOG: dict[str, TemplateMeta] = {
    "line_chart_basic": TemplateMeta(
        id="line_chart_basic",
        name="基础折线图",
        scenario="趋势对比、时间序列",
        description="单/多折线，适合实验组与对照组随时间变化的趋势展示。",
    ),
    "line_chart_report": TemplateMeta(
        id="line_chart_report",
        name="报告风格折线图",
        scenario="论文插图、正式报告",
        description="更大字号与留白，适合嵌入 Word / LaTeX 报告。",
    ),
    "bar_chart_basic": TemplateMeta(
        id="bar_chart_basic",
        name="基础柱状图",
        scenario="类别对比、样本量统计",
        description="纵向柱形，适合多组样本数量或指标对比。",
    ),
    "horizontal_bar_chart": TemplateMeta(
        id="horizontal_bar_chart",
        name="横向柱状图",
        scenario="排名、百分比、长标签",
        description="横向柱形，类别名较长时更易阅读。",
    ),
    "heatmap_basic": TemplateMeta(
        id="heatmap_basic",
        name="基础热力图",
        scenario="相关性、矩阵数据",
        description="颜色映射矩阵数值，适合相关性与表格型数据。",
    ),
    "scatter_chart_basic": TemplateMeta(
        id="scatter_chart_basic",
        name="基础散点图",
        scenario="相关分析、分组分布",
        description="支持多组散点，展示变量间关系与聚类趋势。",
    ),
}


def get_template_meta(template_id: str) -> TemplateMeta:
    if template_id in TEMPLATE_CATALOG:
        meta = TEMPLATE_CATALOG[template_id]
        preview = TEMPLATES_DIR / template_id / "preview.png"
        if preview.is_file():
            return TemplateMeta(
                meta.id, meta.name, meta.scenario, meta.description, preview
            )
        return meta
    return TemplateMeta(
        template_id,
        template_id,
        "自定义模板",
        "ChartStudio 兼容项目。",
    )


def list_template_metas(include_legacy: bool = False) -> List[TemplateMeta]:
    return [get_template_meta(tid) for tid in get_templates(include_legacy=include_legacy)]


def render_template_gallery(key_prefix: str = "gallery") -> str:
    """渲染模板卡片网格，返回当前选中的 template_id。"""
    metas = list_template_metas()
    if not metas:
        st.warning("未找到可用模板。")
        return "line_chart_basic"

    if "new_template" not in st.session_state:
        st.session_state.new_template = metas[0].id

    st.caption("点击卡片选择模板，然后在下方填写保存路径并创建项目。")

    cols_per_row = 3
    for row_start in range(0, len(metas), cols_per_row):
        cols = st.columns(cols_per_row)
        for col, meta in zip(cols, metas[row_start : row_start + cols_per_row]):
            with col:
                selected = st.session_state.new_template == meta.id
                border = "2px solid #1565C0" if selected else "1px solid #ddd"
                st.markdown(
                    f'<div style="border:{border};border-radius:8px;padding:8px;margin-bottom:4px;">'
                    f'<b>{meta.name}</b><br>'
                    f'<span style="color:#888;font-size:0.85rem">{meta.scenario}</span></div>',
                    unsafe_allow_html=True,
                )
                if meta.preview_path and meta.preview_path.is_file():
                    st.image(str(meta.preview_path), use_container_width=True)
                else:
                    st.markdown(
                        '<div style="height:100px;background:#f0f0f0;border-radius:6px;'
                        'display:flex;align-items:center;justify-content:center;color:#999;">'
                        "暂无预览图</div>",
                        unsafe_allow_html=True,
                    )
                st.caption(meta.description[:60] + ("…" if len(meta.description) > 60 else ""))
                if st.button(
                    "选择" if not selected else "✓ 已选",
                    key=f"{key_prefix}_pick_{meta.id}",
                    use_container_width=True,
                    type="primary" if selected else "secondary",
                ):
                    st.session_state.new_template = meta.id
                    st.rerun()

    current = get_template_meta(st.session_state.new_template)
    st.info(f"当前选中：**{current.name}** · {current.scenario}")
    return st.session_state.new_template
