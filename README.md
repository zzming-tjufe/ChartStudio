# ChartStudio

本地科研图表可视化调参工具。

## 界面布局

- **左侧 Sidebar**：打开/新建项目、调整图表样式（独立滚动）
- **主区域**：图表实时预览、导出与保存
- 调参时图表始终保持在主区域可见

## 快速开始

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 字体说明

若中文显示为方框或缺字，请在「图表配置文件」中指定字体路径：

```yaml
font:
  file_path: "C:/Windows/Fonts/simhei.ttf"
```

Windows 常见字体路径：

```text
C:/Windows/Fonts/simhei.ttf
C:/Windows/Fonts/simkai.ttf
C:/Windows/Fonts/msyh.ttc
C:/Windows/Fonts/times.ttf
```

也可将 `.ttf` / `.otf` 放入项目 `fonts/` 目录，例如：

```yaml
font:
  file_path: "fonts/simhei.ttf"
```

字体文件不会随 ChartStudio 打包，需自行准备。

## 项目结构

```text
my_project/
├─ chart_config.yaml
├─ chart_core.py
├─ chart_project.yaml
├─ data/
├─ fonts/
├─ output/
└─ configs/
```

## 标准协议

`chart_core.py` 必须实现 `draw_chart(config)`，只返回 `fig`，不调用 `plt.show()` 或 `fig.savefig()`。

运行时 ChartStudio 会向 config 注入 `_project_root`（不会写入 YAML），读取项目内文件请使用：

```python
from pathlib import Path
root = Path(config["_project_root"])
data_path = root / "data" / "data.csv"
```

## 可用模板

- 基础折线图 `line_chart_basic`
- 报告风格多折线图 `line_chart_report`
- 基础柱状图 `bar_chart_basic`
- 横向柱状图 `horizontal_bar_chart`
- 基础热力图 `heatmap_basic`
- 基础散点图 `scatter_chart_basic`

旧版模板位于 `templates/_legacy/`，默认不在新建列表中显示。
