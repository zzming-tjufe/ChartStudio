# v2 Annotations 验收 — 已知限制

## 分类 X 轴 + `end.coord: data`

验收用例 `chart_config.yaml` 使用**数值 X**（`x: [1, 2, 3, 4, 5]`），
`arrow.end` 的 `x: 4, y: 5.0` 可正确指向数据点。

当 `data.x` 为**字符串类目**（如 `["Jan", "Feb", "Mar"]`）时：

- Matplotlib 会将 X 轴视为分类轴，内部坐标与配置的字符串或索引关系**未在 ChartStudio 协议中定义**。
- `coord: data` 下的 `x`/`y` 目前直接传给 Matplotlib `annotate`，行为依赖底层轴类型，可能出现箭头落点与预期类目不一致。
- **TODO（后续协议/React 画布）**：为分类轴增加显式约定（例如 `x` 使用类目索引、`x_label` 引用类目名，或增加 `coord: category`），并在 `annotations` 文档中说明。

本轮验收不修改渲染逻辑；numeric X 场景已通过 CLI 与 `reproduce.py` 验证。
