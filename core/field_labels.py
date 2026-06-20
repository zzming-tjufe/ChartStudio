"""
配置字段中文可读名称映射。

改动记录与简洁模式控件优先使用此表，无映射时回退到原始路径。
"""

from __future__ import annotations

from typing import Dict

FIELD_LABELS: Dict[str, str] = {
    # 基础信息
    "chart.title": "图表标题",
    "chart.subtitle": "副标题",
    # 画布
    "figure.width": "画布宽度（英寸）",
    "figure.height": "画布高度（英寸）",
    "chart.width": "画布宽度（英寸）",
    "chart.height": "画布高度（英寸）",
    # 导出
    "export.dpi": "导出 DPI",
    "export.transparent": "透明背景",
    "chart.dpi": "导出 DPI",
    # 字体
    "font.zh_name": "中文字体（配置写入标准名，如 Microsoft YaHei）",
    "font.zh_path": "中文字体路径",
    "font.en_name": "英文字体",
    "font.en_path": "英文字体路径",
    "font.num_name": "数字字体",
    "font.num_path": "数字字体路径",
    "font.family": "字体族（兼容）",
    "font.file_path": "字体文件路径（高级覆盖）",
    "font.title_size": "标题字号",
    "font.label_size": "轴标签字号",
    "font.tick_size": "刻度字号",
    "font.legend_size": "图例字号",
    # 坐标轴
    "axes.x_label": "X 轴标题",
    "axes.y_label": "Y 轴标题",
    "axes.grid": "显示网格",
    "axes.grid_alpha": "网格透明度",
    "axes.spine_visible": "显示边框",
    "axes.xlim": "X 轴范围",
    "axes.ylim": "Y 轴范围",
    "axes.y_margin": "Y 轴留白比例",
    # 图例
    "legend.show": "显示图例",
    "legend.loc": "图例位置",
    "legend.frameon": "图例边框",
    "legend.fontsize": "图例字号",
    # 线条
    "line_style.width": "线宽",
    "line_style.line_width": "线宽",
    "line_style.marker_size": "圆点大小",
    "line_style.marker": "标记形状",
    "line_style.marker_edge_width": "标记描边宽度",
    "line_style.alpha": "线条透明度",
    # 柱状图
    "bar_style.width": "柱宽",
    "bar_style.edge_width": "柱边框宽度",
    "bar_style.alpha": "柱透明度",
    # 散点
    "scatter_style.size": "散点大小",
    "scatter_style.alpha": "散点透明度",
    "scatter_style.edge_width": "散点描边",
    # 热力图
    "heatmap.cmap": "色图方案（发散/顺序/打印）",
    "heatmap.annot": "显示数值",
    "heatmap.linewidth": "格子线宽",
    "heatmap.colorbar": "显示色条",
    # 颜色
    "series.overall.color": "主系列颜色",
    # 数据标签
    "data_labels.show": "显示数据标签",
    "data_labels.fontsize": "数据标签字号",
    "data_labels.offset": "标签偏移",
    "data_labels.decimals": "小数位数",
    "data_labels.prefix": "标签前缀",
    "data_labels.suffix": "标签后缀",
    # 自定义文字位置
    "custom_text.title_xy": "标题位置 [x, y]",
    "custom_text.legend_xy": "图例位置 [x, y]",
}


def get_field_label(path: str) -> str:
    """获取字段中文名，支持 series.xxx.color / label 等动态路径。"""
    if path in FIELD_LABELS:
        return FIELD_LABELS[path]

    parts = path.split(".")
    if len(parts) >= 3 and parts[0] == "series" and parts[-1] == "color":
        return f"系列「{parts[1]}」颜色"
    if len(parts) >= 3 and parts[0] == "series" and parts[-1] == "label":
        return f"系列「{parts[1]}」名称"
    if len(parts) >= 3 and parts[0] == "series" and parts[-1] == "label_offset":
        return f"系列「{parts[1]}」标签偏移"

    return path
