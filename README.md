# ChartStudio

面向论文、报告作者的本地图表制图工具。选模板、导入数据、调整样式，实时预览后导出 PNG / SVG / PDF。

当前协议版本：**schema v2**（`chartstudio_version 0.2.0`），支持布局边距、annotations 标注、字体注册表等能力。

**三种入口并存（迁移期）：**

| 入口 | 用途 |
|------|------|
| `streamlit run app.py` | **主应用**：建项目、导数据、调样式、导出 |
| `chartstudio` / `cs` | **CLI**：渲染、校验、导出复现脚本 |
| `frontend/` + `core/api_server.py` | **React 原型**：可视化拖动 annotation，写回 YAML 后 Matplotlib 重渲染 |

Streamlit 仍是日常使用入口；CLI 适合脚本与 CI；React 仅验证「前端编辑 annotations ↔ 配置协议 ↔ 后端渲染」闭环。

## 安装与启动

需要 Python 3.10 及以上。

```bash
pip install -r requirements.txt
pip install -e .          # 推荐：注册 chartstudio / cs 命令（见 pyproject.toml）
streamlit run app.py
```

浏览器会自动打开 ChartStudio 界面。若需导入 Excel，请确保依赖已安装（`requirements.txt` 已包含）。

### 三种入口一览

| 入口 | 命令 | 适合 |
|------|------|------|
| **Streamlit（主应用）** | `streamlit run app.py` | 建项目、导数据、调样式、导出 |
| **CLI** | `chartstudio .` / `cs check .` | 脚本化渲染、CI 校验、无界面批处理 |
| **React 原型** | `uvicorn core.api_server:app` + `frontend` dev | 拖动编辑 annotations，验证协议闭环 |

---

### 命令行（CLI）

在仓库根目录执行 `pip install -e .` 后，使用 **`chartstudio`** 或短别名 **`cs`**。未安装时等价于 `python -m core.cli`。

**路径规则**：`config` 参数可以是**项目目录**（自动找 `chart_config.yaml`）或 **yaml 文件路径**；省略时默认为当前目录 `.`。

| 子命令 | 别名 | 作用 |
|--------|------|------|
| `render` | （省略子命令时默认） | 渲染到图片 |
| `check` | `validate` | 校验配置 + 可选渲染探测 |
| `script` | `export-code` | 生成 `reproduce.py` 复现脚本 |

**常用示例：**

```bash
# 最简：渲染当前目录 → output/chart.png
chartstudio .
cs .

# 指定项目 / 配置文件
chartstudio render examples/v2_annotations_acceptance
chartstudio render path/to/chart_config.yaml

# 格式与输出（-o 可省略）
chartstudio render . -f svg                    # → output/{标题或 chart}.svg
chartstudio render . -o output/custom.png

# 校验
chartstudio check .
chartstudio check . -q                         # 仅输出 ok 或 N error(s), M warn(s)

# 复现脚本（-o 默认 reproduce.py）
chartstudio script .
chartstudio script . -f svg -o reproduce.py
```

**默认输出位置：**

| 命令 | 未指定 `-o` 时 |
|------|----------------|
| `render` | `{项目目录}/output/chart.png`（有图表标题则用标题作文件名） |
| `script` | `{项目目录}/reproduce.py` |

通用选项：`-f png|svg|pdf`、`-t {template_id}`（一般不必填，配置里已有 `template_id`）。

---

### React Annotation Editor（原型，可选）

用于验证：**拖动 annotation → 保存 chart_config.yaml → Matplotlib 重新渲染后位置一致**。不替代 Streamlit，不含数据导入、风格预设等完整功能。

需要 **两个终端**：

```bash
# 终端 1：轻量 API（项目根目录）
uvicorn core.api_server:app --reload --port 8000

# 终端 2：React 前端
cd frontend
npm install   # 首次
npm run dev
```

浏览器打开 http://localhost:5173 ，在顶部输入 `chart_config.yaml` 的**绝对路径**（例如 `examples/v2_annotations_acceptance/chart_config.yaml`），点击 **打开配置**。

| 能力 | 说明 |
|------|------|
| 可编辑 | `text`、`rectangle`（仅 `coord=axes`，画布上拖动 + 右侧属性） |
| 只读 | `arrow`（含 axes / data 混合坐标，暂不支持拖端点） |
| 保存 | 调用 `/api/save-config`，经 `config_validator` 校验后写 YAML |
| 重渲染 | 调用 `/api/render`，Matplotlib 输出 SVG 作为底图 |

API 接口：`/api/open-config`、`/api/render`、`/api/save-config`、`/api/check`。详见 [`frontend/README.md`](frontend/README.md)。

---

## 怎么用（Streamlit）

### 打开或新建项目

启动后首先进入**欢迎页**（不会显示空白图表预览）：

- **新建**：在主区域选择模板卡片 → 填写保存位置 → 创建
- **打开已有项目**，任选一种方式：
  - 输入项目文件夹路径
  - 点击「浏览文件夹」
  - 将 `chart_config.yaml` **拖入**上传区，再点击「定位文件夹并填入路径」或「定位并打开」（在弹窗中选择同一文件即可自动识别所在文件夹）

路径旁会显示状态提示（✅ 可用 / ⚠️ 注意 / ❌ 无法打开）。

打开项目后，ChartStudio 会记住当前项目路径；**刷新浏览器**会自动回到编辑界面（未保存的调参改动不会保留，以磁盘上已保存的配置为准）。若要回到欢迎页，可在侧栏「项目管理」中点击「关闭项目」。

### 导入数据

在左侧 **「数据导入」** 中上传 CSV 或 Excel，按提示选择列名：

| 图表类型 | 需要选择的列 |
|----------|--------------|
| 折线图 | X 轴列 + 一个或多个 Y 轴列 |
| 柱状图 / 横向柱状图 | 类别列 + 数值列 |
| 散点图 | X 列 + Y 列（可选分组列） |
| 热力图 | 数值矩阵，或从多列数值生成相关性矩阵 |

映射完成后点击 **「保存当前配置」**，数据和样式会一并保存到项目中。之后可随时重新上传、重新映射。

### 调整样式

左侧提供两种面板：

- **简洁模式**（推荐）：按「基础信息、画布尺寸、字体、坐标轴、图例、颜色、导出」等分组调参。
- **高级模式**：展开全部配置项，适合精细微调。

**风格预设** 可一键切换整体观感（只改样式，不改数据）：

| 预设 | 适合场景 |
|------|----------|
| 学术论文风 | 投稿、印刷，300 DPI，宋体 + Times |
| 中文报告风 | Word 报告，字号偏大、易读 |
| 蓝色科技风 | 演示、技术文档 |
| 黑白打印风 | 打印、灰度输出 |
| 答辩 PPT 风 | 透明背景、大字号、宽画布 |

### 预览、检查与导出

- 主区域实时显示当前图表。
- 预览下方 **「图表检查」** 会提示字体、DPI、标题、轴标签等是否适合论文/报告出图（✅ 通过 / ⚠️ 提醒 / 💡 建议）。
- 满意后点击 **导出 PNG / SVG / PDF**，文件保存在项目的 **output** 文件夹，也可一键打开该文件夹。

### 保存与恢复

- **保存当前配置**：将本次所有修改写入项目。
- **另存配置快照**：保留某一时刻的配置备份，便于对比或回退。
- **恢复已保存配置**：放弃未保存的修改，回到上次保存的状态。

顶部徽章会提示是否有未保存的改动。

### 让 AI 帮你改图

页面底部 **「让 AI 修改当前图表项目」** 可生成完整提示词：包含当前项目配置和你的修改需求。复制到 ChatGPT、Claude 等工具，让 AI 在现有图表基础上改样式或加功能，而不是从零重写。

---

## 可选模板

| 名称 | 适合做什么 |
|------|------------|
| 基础折线图 | 趋势、时间序列、多组对比 |
| 报告风格折线图 | 论文插图、正式报告 |
| 基础柱状图 | 类别数量、指标对比 |
| 横向柱状图 | 排名、百分比、类别名较长时 |
| 基础热力图 | 相关性、矩阵型数据 |
| 基础散点图 | 变量关系、分组分布 |

新建时以卡片形式展示，含适用场景与简要说明。

---

## 字体与中文字符

ChartStudio 使用**字体注册表**（`core/font_registry.py`）管理「界面显示名」与「可复现的真实字体信息」：

- **界面下拉**显示友好名称，例如：微软雅黑、宋体、黑体、楷体、Times New Roman
- **配置文件**保存 Matplotlib 可识别的 `family` 与字体文件 `path`，避免渲染层猜测中文别名

在左侧 **「字体设置」** 中选择字体后，保存的配置大致如下（`normalize_config` 会自动补齐）：

```yaml
font:
  zh:
    display: "微软雅黑"          # 用户友好显示名
    family: "Microsoft YaHei"  # Matplotlib family
    path: "C:/Windows/Fonts/msyh.ttc"
    source: "system"
  en:
    display: "Times New Roman"
    family: "Times New Roman"
    path: "C:/Windows/Fonts/times.ttf"
    source: "system"
  num:
    display: "Times New Roman"
    family: "Times New Roman"
    path: "C:/Windows/Fonts/times.ttf"
    source: "system"
  # 兼容旧字段（仍保留，勿删）
  zh_name: "Microsoft YaHei"
  zh_path: "C:/Windows/Fonts/msyh.ttc"
  en_name: "Times New Roman"
  num_name: "Times New Roman"
  title_size: 16
  label_size: 12
  tick_size: 10
  legend_size: 10
```

英文、数字字体可分别设置；论文常用 **Times New Roman** 搭配 **宋体** 或 **微软雅黑**。

高级选项中可手动指定 `font.file_path` 覆盖中文字体文件（例如项目 `fonts/` 目录下的自定义字体）。

若中文显示为方框，请在「字体设置」中重新选择中文字体，并确认预览区「图表检查」中的字体诊断无 ⚠️。

---

## 配置协议（v2 概要）

每个图表项目的核心是 `chart_config.yaml`，由 ChartStudio 与 AI 共同维护。v2 主要字段：

| 字段 | 说明 |
|------|------|
| `schema_version` | 当前为 `2` |
| `template_id` | 模板 ID，如 `line_chart_basic` |
| `chartstudio_version` | ChartStudio 版本号 |
| `data` | 图表数据 |
| `figure` | 画布宽高（英寸） |
| `export` | `dpi`、`transparent`、`bbox`（`fixed` / `tight`） |
| `layout` | 边距 `left/right/bottom/top`、`use_tight_layout` |
| `font` | 字体（见上文注册表结构） |
| `axes` / `legend` / `series` | 坐标轴、图例、系列样式 |
| `annotations` | 文本、箭头、矩形等叠加标注 |

`annotations` 示例（text / arrow / rectangle）见 `examples/v2_annotations_acceptance/`。React 原型可在该示例上拖动 `coord=axes` 的 text / rectangle 做往返验证。

打开旧版配置时，`normalize_config` 会自动迁移字段（如 `chart.width` → `figure.width`、`chart.dpi` → `export.dpi`），并补齐 `layout`、`annotations`、`font.zh/en/num` 等结构。

---

## 常见问题

**中文乱码或缺字？**  
在「字体设置」里重新选择中文字体；保存后检查 `font.zh.path` 是否指向有效字体文件。

**Excel 上传失败？**  
确认文件格式为 `.xlsx` 或 `.xls`，并重新执行 `pip install -r requirements.txt`。

**改了样式但预览没变？**  
确认已点击「保存当前配置」；若仍异常，在「项目管理」中尝试「重新加载项目」。

**导出图片不够清晰？**  
在「导出设置」中将 DPI 设为 300，或使用「学术论文风」预设。

**透明背景适合什么场景？**  
适合插入 PPT；Word 排版或打印建议关闭透明背景。

**React 原型打不开配置？**  
确认 API 已在 8000 端口运行；路径必须是本机可访问的绝对路径；前端 dev 服务器通过 Vite 代理访问 `/api`。

**`chartstudio` 命令找不到？**  
在仓库根目录执行 `pip install -e .`；或改用 `python -m core.cli`。

**CLI 提示找不到 chart_config.yaml？**  
确认当前目录是项目文件夹，或直接传入 yaml 路径 / 含配置的目录路径。

---

## 项目文件夹里有什么

新建项目后，你主要会用到：

| 路径 | 说明 |
|------|------|
| `chart_config.yaml` | 图表配置（数据 + 样式 + 协议字段） |
| `chart_core.py` | 绘图逻辑（通常由模板复制，可按需修改） |
| `output/` | 导出的图片（PNG / SVG / PDF） |
| `data/` | 导入的数据文件备份 |
| `fonts/` | 可选，放置自定义字体文件 |
| `configs/` | 配置快照备份 |

仓库根目录另有 `frontend/`（React 原型源码）与 `pyproject.toml`（CLI 入口 `chartstudio` / `cs`），不属于单个图表项目。

其余文件由 ChartStudio 自动维护。一般只需关心 `output` 与 `data`；进阶用户或 AI 协作时可编辑 `chart_config.yaml`。

---

## 开发者 / 架构说明

逻辑集中在 `core/`，Streamlit 界面（`app.py`）只做编排；React 原型通过薄 API 复用同一套 `render_service` 与配置协议。

| 模块 | 作用 |
|------|------|
| `app.py` | Streamlit 主入口（编排，非业务核心） |
| `core/render_service.py` | 统一渲染入口（Streamlit / CLI / API 共用） |
| `core/api_server.py` | FastAPI：open-config / render / save-config / check |
| `core/font_registry.py` | 字体注册表与 display/family/path 解析 |
| `core/font_utils.py` | `FontProperties` 解析与字体诊断 |
| `core/config_migrate.py` | 配置规范化与 v2 迁移 |
| `core/config_validator.py` | 保存前校验（含 annotations 协议） |
| `core/layout.py` / `core/annotations.py` | 布局与标注 |
| `core/cli.py` | 命令行入口（`chartstudio` / `cs` / `python -m core.cli`） |
| `core/cli_paths.py` | CLI 项目路径解析与默认输出路径 |
| `frontend/` | React + Zustand；SVG 底图 + overlay 编辑 annotations |
| `templates/*/` | 各图表模板（`chart_config.yaml` + `chart_core.py`） |

验收示例：`examples/v2_annotations_acceptance/`（含 `reproduce.py`；亦可作为 React 原型测试配置）。
