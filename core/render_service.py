"""统一图表渲染入口 — 无 Streamlit 依赖。"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

from core.config_loader import load_yaml
from core.config_migrate import normalize_config
from core.dynamic_importer import import_draw_chart
from core.font_runtime import apply_chart_fonts, prepare_chart_fonts
from core.project_manager import DEFAULT_TEMPLATE, _resolve_template_path


def resolve_template_core_path(template_id: str) -> Path:
    """模板目录下的 chart_core.py。"""
    tid = template_id or DEFAULT_TEMPLATE
    template_dir = _resolve_template_path(tid)
    if template_dir is None:
        raise FileNotFoundError(f"找不到模板：{tid}")

    template_core = template_dir / "chart_core.py"
    if not template_core.is_file():
        raise FileNotFoundError(f"模板缺少 chart_core.py：{template_core}")
    return template_core.resolve()


def resolve_chart_core_path(
    project_root: Path,
    template_id: str,
) -> Path:
    """
    解析 chart_core.py 路径。

    优先项目目录（与 chart_config.yaml 同目录），否则回退模板目录。
    """
    local_core = project_root / "chart_core.py"
    if local_core.is_file():
        return local_core.resolve()

    return resolve_template_core_path(template_id)


def resolve_core_path_for_render(
    template_id: str,
    *,
    core_path: Path | None = None,
    project_root: Path | None = None,
) -> Path:
    """
    解析渲染用的 chart_core.py。

    1. 显式 core_path
    2. project_root 下 local core，再模板
    3. 仅 template_id 对应模板目录
    """
    if core_path is not None:
        resolved = Path(core_path).expanduser().resolve()
        if resolved.is_file():
            return resolved
        raise FileNotFoundError(f"chart_core.py 不存在：{resolved}")

    if project_root is not None:
        return resolve_chart_core_path(project_root.resolve(), template_id)

    return resolve_template_core_path(template_id)


def render_chart_from_config(
    config: Dict[str, Any],
    template_id: str | None = None,
    *,
    core_path: Path | None = None,
    project_root: Path | None = None,
) -> Any:
    """从配置 dict 渲染图表，返回 Matplotlib Figure。"""
    tid = (template_id or config.get("template_id") or DEFAULT_TEMPLATE).strip()
    cfg = deepcopy(config)

    root = project_root
    if root is None:
        raw_root = cfg.get("_project_root")
        if raw_root:
            root = Path(str(raw_root)).resolve()
    if root is not None:
        cfg["_project_root"] = str(root)

    normalized, _ = normalize_config(cfg, template_id=tid)

    resolved_core = resolve_core_path_for_render(
        tid,
        core_path=core_path,
        project_root=root,
    )

    draw_fn = import_draw_chart(resolved_core, purge_old=False)
    font_bundle = prepare_chart_fonts(normalized)
    fig = draw_fn(normalized)
    if fig is not None:
        apply_chart_fonts(fig, normalized)
    return fig


def render_chart_from_file(
    config_path: str | Path,
    template_id: str | None = None,
) -> Any:
    """从 chart_config.yaml 路径渲染，自动解析项目根目录与 chart_core.py。"""
    path = Path(config_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"配置文件不存在：{path}")

    project_root = path.parent
    config = load_yaml(path)
    config["_project_root"] = str(project_root)

    tid = (template_id or config.get("template_id") or DEFAULT_TEMPLATE).strip()
    core_path = resolve_chart_core_path(project_root, tid)
    return render_chart_from_config(
        config,
        template_id=tid,
        core_path=core_path,
        project_root=project_root,
    )
