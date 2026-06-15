"""
项目创建、打开与校验模块。
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from core.config_loader import load_yaml

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
LEGACY_TEMPLATES_DIR = TEMPLATES_DIR / "_legacy"
DEFAULT_TEMPLATE = "line_chart_basic"

REQUIRED_FILES = ("chart_config.yaml", "chart_core.py")
OPTIONAL_FILES = ("chart_project.yaml",)

# 默认模板列表（不含旧版）
DEFAULT_TEMPLATE_IDS = [
    "line_chart_basic",
    "line_chart_report",
    "bar_chart_basic",
    "horizontal_bar_chart",
    "heatmap_basic",
    "scatter_chart_basic",
]

TEMPLATE_DISPLAY_NAMES = {
    "line_chart": "多折线图（旧版 · 兼容）",
    "line_chart_basic": "基础折线图",
    "line_chart_report": "报告风格多折线图",
    "bar_chart_basic": "基础柱状图",
    "horizontal_bar_chart": "横向柱状图",
    "heatmap_basic": "基础热力图",
    "scatter_chart_basic": "基础散点图",
}


@dataclass
class ProjectInfo:
    root: Path
    config_path: Path
    core_path: Path
    project_meta_path: Optional[Path]
    is_compatible_mode: bool
    meta: dict

    @property
    def template_name(self) -> str:
        tpl = self.meta.get("template", "")
        return TEMPLATE_DISPLAY_NAMES.get(tpl, tpl or "未知模板")

    @property
    def display_name(self) -> str:
        return self.meta.get("name", self.root.name)

    @property
    def template_id(self) -> str:
        return str(self.meta.get("template", ""))


def _resolve_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def get_templates(include_legacy: bool = False) -> List[str]:
    if not TEMPLATES_DIR.is_dir():
        return []
    ids = [tid for tid in DEFAULT_TEMPLATE_IDS if (TEMPLATES_DIR / tid).is_dir()]
    if include_legacy and LEGACY_TEMPLATES_DIR.is_dir():
        legacy = sorted(p.name for p in LEGACY_TEMPLATES_DIR.iterdir() if p.is_dir())
        ids.extend(legacy)
    return ids


def get_template_choices(include_legacy: bool = False) -> List[tuple[str, str]]:
    ids = get_templates(include_legacy=include_legacy)
    return [(tid, TEMPLATE_DISPLAY_NAMES.get(tid, tid)) for tid in ids]


def validate_project(path: str | Path) -> Tuple[bool, str, Optional[ProjectInfo]]:
    root = _resolve_path(path)

    if not root.is_dir():
        return False, f"找不到该文件夹：{root}", None

    config_path = root / "chart_config.yaml"
    core_path = root / "chart_core.py"
    project_meta_path = root / "chart_project.yaml"

    missing = [name for name in REQUIRED_FILES if not (root / name).is_file()]
    if missing:
        labels = {"chart_config.yaml": "图表配置文件", "chart_core.py": "绘图核心文件"}
        missing_labels = [labels.get(m, m) for m in missing]
        return False, f"缺少必需文件：{', '.join(missing_labels)}", None

    is_compatible = not project_meta_path.is_file()
    meta = {}
    if project_meta_path.is_file():
        try:
            meta = load_yaml(project_meta_path)
        except Exception as exc:
            return False, f"无法读取项目说明文件：{exc}", None

    info = ProjectInfo(
        root=root,
        config_path=config_path,
        core_path=core_path,
        project_meta_path=project_meta_path if not is_compatible else None,
        is_compatible_mode=is_compatible,
        meta=meta,
    )
    name = info.display_name
    if is_compatible:
        return True, f"已加载基础项目「{name}」（缺少项目说明文件）", info
    return True, f"已打开项目「{name}」", info


def _resolve_template_path(template_name: str) -> Optional[Path]:
    primary = TEMPLATES_DIR / template_name
    if primary.is_dir():
        return primary
    legacy = LEGACY_TEMPLATES_DIR / template_name
    if legacy.is_dir():
        return legacy
    return None


def create_project(
    target_dir: str | Path,
    template_name: str = DEFAULT_TEMPLATE,
    project_name: Optional[str] = None,
) -> Tuple[bool, str, Optional[ProjectInfo]]:
    root = _resolve_path(target_dir)
    template_path = _resolve_template_path(template_name)

    if template_path is None:
        return False, f"模板不存在：{template_name}", None

    if root.exists() and any(root.iterdir()):
        return False, f"目标文件夹非空，请选择空文件夹：{root}", None

    root.mkdir(parents=True, exist_ok=True)

    for filename in ("chart_config.yaml", "chart_core.py", "chart_project.yaml"):
        src = template_path / filename
        if src.is_file():
            shutil.copy2(src, root / filename)

    for sub in ("data", "fonts", "output", "configs"):
        (root / sub).mkdir(exist_ok=True)

    if project_name:
        project_yaml = root / "chart_project.yaml"
        if project_yaml.is_file():
            from core.config_loader import save_yaml

            meta = load_yaml(project_yaml)
            meta["name"] = project_name
            save_yaml(project_yaml, meta)

    ok, msg, info = validate_project(root)
    if ok:
        return True, f"项目已创建：{root}", info
    return False, msg, None
