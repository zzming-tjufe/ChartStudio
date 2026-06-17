"""
AI 提示词 — 基于当前项目动态生成修改提示。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from core.config_loader import strip_internal_keys

CORE_PROTOCOL = """
## chart_core.py 协议（ChartStudio 标准）

- 必须包含：`def draw_chart(config):`
- 所有样式与数据从 `config` 字典读取，不要硬编码
- 只返回 Matplotlib 的 `fig` 对象
- **禁止** `plt.show()`、`fig.savefig()` / `plt.savefig()`
- **禁止**在 `draw_chart` 内处理字体（字体由 ChartStudio 主程序统一注入）
- 不要在模块顶层产生绘图副作用
"""

GENERIC_CREATE_PROMPT = """你是一名 Python 科研绘图专家。请生成一个兼容 ChartStudio 的 Matplotlib 图表项目。

## 必须输出的文件

1. chart_config.yaml — 可调参数（含 data、font、axes、export 等）
2. chart_core.py — 绘图核心（遵循下方协议）
3. chart_project.yaml — 项目说明

""" + CORE_PROTOCOL + """

## 我的图表需求

（在此描述图表类型、数据、风格等）

请分别输出三个文件的完整内容。
"""


def get_ai_prompt() -> str:
    """兼容旧接口：无项目时的通用创建提示词。"""
    return GENERIC_CREATE_PROMPT


def get_ai_prompt_for_project(
    config: Dict[str, Any],
    template_id: str,
    template_label: str,
    core_source: str,
    project_name: str = "",
    user_request: str = "",
) -> str:
    """基于当前打开的项目生成「让 AI 修改当前图表」的完整提示词。"""
    yaml_text = yaml.dump(
        strip_internal_keys(config),
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    request_block = user_request.strip() or "（请在此填写你想让 AI 修改的内容，例如：加误差棒、改配色、调整字号…）"

    return f"""你是一名 Python 科研绘图专家。我正在使用 ChartStudio 本地调参工具编辑图表项目，请你**在现有项目基础上修改**，而不是从零重写无关结构。

## 当前项目信息

- 项目名称：{project_name or "（未命名）"}
- 模板类型：`{template_id}`（{template_label}）

## 当前 chart_config.yaml

```yaml
{yaml_text}
```

## 当前 chart_core.py

```python
{core_source}
```

{CORE_PROTOCOL}

## 我的修改需求

{request_block}

## 修改原则（必须遵守）

1. **只修改必要文件**：通常仅需 `chart_config.yaml` 与 `chart_core.py`；不要改动 ChartStudio 项目目录结构（`data/`、`fonts/`、`configs/`、`output/` 等）。
2. **保留基础协议字段**：不得删除 `schema_version`、`template_id`、`chartstudio_version`、`data`、`font`、`axes`、`export`、`figure` 等 ChartStudio 依赖字段；可增补但不可破坏既有键。
3. **向后兼容**：`draw_chart(config)` 中读取的任何**新增**配置字段，必须用 `.get()` 并提供合理缺省值，确保旧配置仍可渲染。
4. **不要破坏项目结构**：不要重命名核心文件、不要移除 `draw_chart`、不要在 `chart_core.py` 中处理字体或执行 `savefig`/`show`。
5. **数据与系列一致**：修改 `data` 时同步考虑 `series` 键名与标签；折线/柱状/散点/热力图数据结构须与模板约定一致。
6. **优先小步修改**：在现有代码上增量调整，避免整文件重写导致无关回归。

## 输出要求

1. 给出修改后的 **chart_config.yaml** 完整内容（保留 ChartStudio 兼容结构，含 `data` 段及 schema 元数据）
2. 给出修改后的 **chart_core.py** 完整内容（仍只含 `draw_chart(config)`，不处理字体；新增字段需缺省兼容）
3. 若需调整项目说明，给出 **chart_project.yaml**
4. 简要说明你改了什么、为什么，并列出 touched 文件清单

请直接输出可复制的完整文件内容。
"""


def read_core_source(core_path: Path) -> str:
    if core_path.is_file():
        return core_path.read_text(encoding="utf-8")
    return "# （无法读取 chart_core.py）"
