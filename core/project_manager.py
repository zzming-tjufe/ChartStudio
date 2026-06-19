"""
项目创建、打开与校验模块。
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from core.config_loader import load_yaml
from core.template_registry import (
    DEFAULT_TEMPLATE_IDS,
    get_template_display_name,
)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
LEGACY_TEMPLATES_DIR = TEMPLATES_DIR / "_legacy"
DEFAULT_TEMPLATE = "line_chart_basic"

REQUIRED_FILES = ("chart_config.yaml", "chart_core.py")
OPTIONAL_FILES = ("chart_project.yaml",)


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
        return get_template_display_name(tpl) if tpl else "未知模板"

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
    return [(tid, get_template_display_name(tid)) for tid in ids]


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
    parent_dir: str | Path,
    template_name: str = DEFAULT_TEMPLATE,
    project_name: Optional[str] = None,
) -> Tuple[bool, str, Optional[ProjectInfo]]:
    """
    在 parent_dir 下创建以项目名命名的子文件夹，并写入模板内容。

    parent_dir: 用户选定的父目录
    project_name: 子文件夹名（同时写入 chart_project.yaml 的 name）
    """
    from core.path_utils import default_project_folder_name, resolve_project_root, sanitize_project_name

    parent = _resolve_path(parent_dir)
    template_path = _resolve_template_path(template_name)

    if template_path is None:
        return False, f"模板不存在：{template_name}", None

    folder_name = sanitize_project_name(project_name or "") or default_project_folder_name(template_name)
    try:
        root = resolve_project_root(parent, folder_name)
    except ValueError as exc:
        return False, str(exc), None

    if root.exists() and any(root.iterdir()):
        return False, f"项目文件夹已存在且非空：{root}", None

    parent.mkdir(parents=True, exist_ok=True)
    root.mkdir(parents=True, exist_ok=True)

    for filename in ("chart_config.yaml", "chart_core.py", "chart_project.yaml"):
        src = template_path / filename
        if src.is_file():
            shutil.copy2(src, root / filename)

    for sub in ("data", "fonts", "output", "configs"):
        (root / sub).mkdir(exist_ok=True)

    project_yaml = root / "chart_project.yaml"
    if project_yaml.is_file():
        from core.config_loader import save_yaml

        meta = load_yaml(project_yaml)
        meta["name"] = sanitize_project_name(project_name or "") or folder_name
        save_yaml(project_yaml, meta)

    ok, msg, info = validate_project(root)
    if ok:
        return True, f"项目已创建：{root}", info
    return False, msg, None
