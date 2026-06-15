"""
AI 兼容项目生成提示词。
"""

from __future__ import annotations

AI_COMPAT_PROMPT = """你是一名 Python 科研绘图专家。请为我生成一个兼容 ChartStudio 本地调参工具的 Matplotlib 图表项目。

## 必须输出的文件

请分别给出以下三个文件的完整内容：

1. chart_config.yaml — 所有可调参数（字号、颜色、线宽、画布尺寸、坐标轴、图例等）
2. chart_core.py — 绘图核心代码
3. chart_project.yaml — 项目说明（name、template、version、description）

## chart_core.py 硬性要求

- 必须包含函数：`def draw_chart(config):`
- 函数内所有样式参数从 `config` 字典读取，不要硬编码
- 只返回 Matplotlib 的 `fig` 对象
- **禁止** 调用 `plt.show()`
- **禁止** 调用 `fig.savefig()` 或 `plt.savefig()`
- 不要在函数外执行绘图副作用

## chart_config.yaml 建议结构

```yaml
chart:
  title: "图表标题"
figure:
  width: 10.0
  height: 6.0
export:
  dpi: 300
font:
  zh_name: "微软雅黑"
  zh_path: ""
  en_name: "Times New Roman"
  en_path: ""
  num_name: "Times New Roman"
  num_path: ""
  family: "sans-serif"
  file_path: ""
  title_size: 16
  label_size: 12
  tick_size: 10
  legend_size: 10
axes:
  x_label: "X 轴"
  y_label: "Y 轴"
  grid: true
  grid_alpha: 0.3
legend:
  show: true
  loc: "best"
line_style:
  width: 2.0
  marker_size: 6.0
series:
  overall:
    color: "#1565C0"
data:
  # 你的数据
```

## chart_project.yaml 示例

```yaml
name: "我的图表"
template: custom
version: "1.0"
description: "由 AI 生成的 ChartStudio 兼容项目"
```

## 我的图表需求

（在此描述：图表类型、数据含义、风格要求、中文标签等）

请直接输出三个文件的完整代码块，便于我复制保存到同一文件夹后，用 ChartStudio 打开调参。
"""


def get_ai_prompt() -> str:
    return AI_COMPAT_PROMPT
