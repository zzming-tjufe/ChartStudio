"""字体解析工具 — 统一中文 FontProperties 与诊断。"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

from matplotlib.font_manager import FontProperties, fontManager

from core.font_registry import (
    diagnose_font_role,
    normalize_font_roles,
    resolve_font_option,
    ROLE_FALLBACK_ORDER,
    FONT_REGISTRY,
)
from core.system_fonts import resolve_font_path_by_name


def _project_root(config: Dict[str, Any]) -> Path:
    return Path(config.get("_project_root", ".")).resolve()


def resolve_path_on_disk(path_str: str, project_root: Path) -> Optional[Path]:
    if not path_str or not str(path_str).strip():
        return None
    raw = Path(str(path_str).strip())
    if raw.is_file():
        return raw.resolve()
    for candidate in (project_root / raw, project_root / "fonts" / raw.name):
        if candidate.is_file():
            return candidate.resolve()
    return None


def contains_cjk(text: Any) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in str(text))


def _register_font_file(path: Path) -> None:
    if path.is_file():
        try:
            fontManager.addfont(str(path))
        except (OSError, ValueError, RuntimeError):
            pass


def _fp_from_path(path: Path, size: Optional[float] = None) -> FontProperties:
    _register_font_file(path)
    return FontProperties(fname=str(path.resolve()), size=size)


def _fp_from_family(family: str, size: Optional[float] = None) -> FontProperties:
    resolved = resolve_font_path_by_name(family)
    if resolved and Path(resolved).is_file():
        return _fp_from_path(Path(resolved), size)
    return FontProperties(family=family, size=size)


def _role_block(font_cfg: Dict[str, Any], role: str) -> Dict[str, Any]:
    block = font_cfg.get(role)
    return block if isinstance(block, dict) else {}


def _registry_fallback_path(role: str, project_root: Path) -> Optional[Path]:
    for reg_id in ROLE_FALLBACK_ORDER.get(role, []):
        entry = FONT_REGISTRY.get(reg_id)
        if not entry or role not in entry.get("role", []):
            continue
        for candidate in entry.get("path_candidates", []):
            disk = resolve_path_on_disk(str(candidate), project_root)
            if disk and disk.is_file():
                return disk
    return None


def resolve_font_properties(
    config: Dict[str, Any],
    role: str = "zh",
    size: Optional[float] = None,
    *,
    warn: bool = True,
) -> Optional[FontProperties]:
    """
    解析字体为 FontProperties。

    优先级：
    1. font[role].path
    2. font[role].family（经注册表 path_candidates / 系统 catalog）
    3. 旧字段 zh_path / zh_name 等
    4. 注册表 fallback 链
    """
    font_cfg = config.get("font", {}) if isinstance(config.get("font"), dict) else {}
    project_root = _project_root(config)
    block = _role_block(font_cfg, role)

    path_candidates: List[str] = []
    if block.get("path"):
        path_candidates.append(str(block["path"]))
    if role == "zh":
        legacy = str(font_cfg.get("file_path", "") or "")
        if legacy:
            path_candidates.append(legacy)

    path_key = f"{role}_path"
    legacy_path = str(font_cfg.get(path_key, "") or "")
    if legacy_path:
        path_candidates.append(legacy_path)

    for raw_path in path_candidates:
        disk = resolve_path_on_disk(raw_path, project_root)
        if disk and disk.is_file():
            return _fp_from_path(disk, size)

    family = str(block.get("family", "") or "")
    if family:
        fp = _fp_from_family(family, size)
        try:
            fname = fp.get_file()
        except Exception:
            fname = None
        if fname and Path(fname).is_file():
            return fp

    name_key = f"{role}_name"
    legacy_name = str(font_cfg.get(name_key, "") or "")
    if legacy_name:
        resolved = resolve_font_option(
            legacy_name,
            role,
            project_root=project_root,
            warn=False,
        )
        if resolved.get("path"):
            disk = resolve_path_on_disk(resolved["path"], project_root)
            if disk and disk.is_file():
                return _fp_from_path(disk, size)
        if resolved.get("family"):
            fp = _fp_from_family(resolved["family"], size)
            try:
                fname = fp.get_file()
            except Exception:
                fname = None
            if fname and Path(fname).is_file():
                return fp

    fallback_disk = _registry_fallback_path(role, project_root)
    if fallback_disk:
        if warn:
            warnings.warn(
                f"字体 role={role} 使用注册表 fallback：{fallback_disk}",
                stacklevel=2,
            )
        return _fp_from_path(fallback_disk, size)

    if warn:
        role_label = {"zh": "中文", "en": "英文", "num": "数字"}.get(role, role)
        warnings.warn(
            f"无法解析{role_label}字体，图表可能出现方块字。",
            stacklevel=2,
        )
    return FontProperties(family="sans-serif", size=size)


def font_properties_for_text(
    config: Dict[str, Any],
    text: Any,
    *,
    zh_size: float,
    en_size: Optional[float] = None,
    num_size: Optional[float] = None,
    warn: bool = False,
) -> FontProperties:
    """按文本内容选择 zh / en / num 字体。"""
    if contains_cjk(text):
        fp = resolve_font_properties(config, "zh", zh_size, warn=warn)
        return fp or FontProperties(family="sans-serif", size=zh_size)

    stripped = str(text).strip().replace(".", "").replace("-", "").replace(",", "")
    if stripped.isdigit():
        size = num_size if num_size is not None else zh_size
        fp = resolve_font_properties(config, "num", size, warn=warn)
        return fp or FontProperties(family="sans-serif", size=size)

    if any(ch.isalpha() for ch in str(text)):
        size = en_size if en_size is not None else zh_size
        fp = resolve_font_properties(config, "en", size, warn=warn)
        return fp or FontProperties(family="sans-serif", size=size)

    size = num_size if num_size is not None else zh_size
    fp = resolve_font_properties(config, "num", size, warn=warn)
    return fp or FontProperties(family="sans-serif", size=size)


def annotation_text_fontproperties(
    config: Optional[Dict[str, Any]],
    style: Dict[str, Any],
    default_size: int = 10,
) -> Optional[FontProperties]:
    """annotation 文本字体：style.font_path 优先，否则 zh。"""
    font_path = str(style.get("font_path", "") or "").strip()
    size = float(style.get("font_size", default_size))
    if font_path:
        raw = Path(font_path)
        if raw.is_file():
            return _fp_from_path(raw, size)
        if config is not None:
            disk = resolve_path_on_disk(font_path, _project_root(config))
            if disk and disk.is_file():
                return _fp_from_path(disk, size)
    if config is None:
        return FontProperties(family="sans-serif", size=size)
    return resolve_font_properties(config, "zh", size)


def apply_legend_fonts(ax, config: Dict[str, Any], size: Optional[float] = None) -> None:
    """图例文字统一使用中文字体。"""
    legend = ax.get_legend()
    if legend is None:
        return
    font_cfg = config.get("font", {}) if isinstance(config.get("font"), dict) else {}
    legend_size = float(size if size is not None else font_cfg.get("legend_size", 10))
    fp = resolve_font_properties(config, "zh", legend_size, warn=False)
    if fp is None:
        return
    for text in legend.get_texts():
        text.set_fontproperties(fp)


def check_font_availability(config: Dict[str, Any]) -> List[str]:
    """字体诊断信息列表（区分 display / family / path / 状态）。"""
    font_cfg = config.get("font", {}) if isinstance(config.get("font"), dict) else {}
    lines: List[str] = []
    for role in ("zh", "en", "num"):
        lines.extend(diagnose_font_role(font_cfg, role, config))
    return lines


def ensure_font_config_normalized(config: Dict[str, Any], warn: bool = False) -> List[str]:
    """补齐 font.zh/en/num 结构（供 normalize_config 调用）。"""
    font_cfg = config.get("font")
    if not isinstance(font_cfg, dict):
        return []
    return normalize_font_roles(font_cfg, project_root=_project_root(config), warn=warn)
