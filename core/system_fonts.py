"""
系统字体目录 — 从 Windows 注册表解析可用字体及真实文件路径。
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional

FONT_EXTENSIONS = {".ttf", ".ttc", ".otf"}

PREFERRED_ZH: List[str] = ["微软雅黑", "黑体", "宋体", "楷体"]
PREFERRED_EN: List[str] = ["Times New Roman", "Arial", "Calibri"]
PREFERRED_NUM: List[str] = ["Times New Roman", "Arial", "Calibri"]

# 注册表/英文名 → 下拉显示名
DISPLAY_ALIASES: Dict[str, str] = {
    "Microsoft YaHei": "微软雅黑",
    "Microsoft YaHei UI": "微软雅黑",
    "MS YaHei": "微软雅黑",
    "SimHei": "黑体",
    "SimSun": "宋体",
    "NSimSun": "新宋体",
    "KaiTi": "楷体",
    "FangSong": "仿宋",
    "Times New Roman": "Times New Roman",
    "Arial": "Arial",
    "Calibri": "Calibri",
    "Courier New": "Courier New",
}

REGISTRY_SUBKEY = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"

SUBSTRING_ALIAS_RULES: List[tuple[str, str]] = [
    ("microsoft yahei", "微软雅黑"),
    ("simhei", "黑体"),
    ("simsun", "宋体"),
    ("kaiti", "楷体"),
    ("times new roman", "Times New Roman"),
    ("arial", "Arial"),
    ("calibri", "Calibri"),
]

LOOKUP_HINTS: Dict[str, List[str]] = {
    "微软雅黑": ["microsoft yahei", "msyh"],
    "黑体": ["simhei"],
    "宋体": ["simsun", "nsimsun"],
    "楷体": ["kaiti", "simkai"],
    "Times New Roman": ["times new roman", "times.ttf"],
    "Arial": ["arial"],
    "Calibri": ["calibri"],
}


def _windows_fonts_dir() -> Path:
    return Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"


def _clean_registry_name(name: str) -> str:
    return re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()


def _to_display_name(registry_name: str) -> str:
    base = _clean_registry_name(registry_name)
    if base in DISPLAY_ALIASES:
        return DISPLAY_ALIASES[base]
    lowered = base.lower()
    for needle, display in SUBSTRING_ALIAS_RULES:
        if needle in lowered:
            return display
    return base


def _registry_rank(registry_name: str) -> int:
    lower = _clean_registry_name(registry_name).lower()
    if any(tag in lower for tag in ("bold", "light", "italic", "oblique", "black", "semibold")):
        return 0
    if "&" in registry_name:
        return 3
    return 2


def _expand_registry_value(value: str) -> Path:
    expanded = os.path.expandvars(value.strip().strip('"'))
    path = Path(expanded)
    if not path.is_absolute():
        path = _windows_fonts_dir() / path
    return path


def _is_valid_font_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in FONT_EXTENSIONS


def _read_windows_registry_fonts() -> Dict[str, Path]:
    if os.name != "nt":
        return {}

    import winreg

    found: Dict[str, Path] = {}
    ranks: Dict[str, int] = {}
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(hive, REGISTRY_SUBKEY) as key:
                index = 0
                while True:
                    try:
                        reg_name, reg_value, _ = winreg.EnumValue(key, index)
                        index += 1
                    except OSError:
                        break
                    if not isinstance(reg_value, str):
                        continue
                    candidate = _expand_registry_value(reg_value)
                    if not _is_valid_font_file(candidate):
                        continue
                    display = _to_display_name(reg_name)
                    rank = _registry_rank(reg_name)
                    if display not in found or rank > ranks.get(display, 0):
                        found[display] = candidate.resolve()
                        ranks[display] = rank
        except OSError:
            continue
    return found


def _scan_font_directories() -> Dict[str, Path]:
    """非 Windows 或注册表不可用时的兜底扫描。"""
    found: Dict[str, Path] = {}
    dirs: List[Path] = []
    if os.name == "nt":
        dirs.append(_windows_fonts_dir())
    dirs.extend(
        [
            Path("/Library/Fonts"),
            Path("/System/Library/Fonts"),
            Path.home() / "Library/Fonts",
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
        ]
    )
    for directory in dirs:
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if not _is_valid_font_file(path):
                continue
            display = DISPLAY_ALIASES.get(path.stem, path.stem)
            found.setdefault(display, path.resolve())
    return found


@lru_cache(maxsize=1)
def get_font_catalog() -> Dict[str, str]:
    """返回 {显示名称: 绝对路径}，仅包含真实存在的字体文件。"""
    catalog_paths: Dict[str, Path] = {}
    if os.name == "nt":
        catalog_paths.update(_read_windows_registry_fonts())
    scanned = _scan_font_directories()
    for name, path in scanned.items():
        catalog_paths.setdefault(name, path)
    return {name: str(path) for name, path in sorted(catalog_paths.items(), key=lambda x: x[0].lower())}


def sort_font_names(names: Iterable[str], preferred: List[str]) -> List[str]:
    name_set = set(names)
    head = [n for n in preferred if n in name_set]
    tail = sorted(n for n in name_set if n not in head)
    return head + tail


def resolve_font_path_by_name(name: str) -> Optional[str]:
    if not name:
        return None
    catalog = get_font_catalog()
    if name in catalog:
        return catalog[name]
    alias = DISPLAY_ALIASES.get(name)
    if alias and alias in catalog:
        return catalog[alias]
    lowered = name.lower()
    for display, path in catalog.items():
        if display.lower() == lowered:
            return path
    for hint in LOOKUP_HINTS.get(name, []):
        hint_lower = hint.lower()
        for display, path in catalog.items():
            if hint_lower in display.lower() or hint_lower in Path(path).name.lower():
                return path
    return None


def resolve_font_with_priority(name: str, priority: List[str]) -> Optional[str]:
    path = resolve_font_path_by_name(name)
    if path:
        return path
    for candidate in priority:
        path = resolve_font_path_by_name(candidate)
        if path:
            return path
    return None


def ensure_font_defaults(font_cfg: Dict[str, object]) -> None:
    """为缺失字段填充默认名称与可解析路径（原地修改）。"""
    defaults = {
        "zh_name": ("微软雅黑", PREFERRED_ZH),
        "en_name": ("Times New Roman", PREFERRED_EN),
        "num_name": ("Times New Roman", PREFERRED_NUM),
    }
    for name_key, (default_name, priority) in defaults.items():
        path_key = name_key.replace("_name", "_path")
        if not font_cfg.get(name_key):
            font_cfg[name_key] = default_name
        if not font_cfg.get(path_key):
            resolved = resolve_font_with_priority(str(font_cfg[name_key]), priority)
            if resolved:
                font_cfg[path_key] = resolved

    font_cfg.setdefault("family", "sans-serif")
    font_cfg.setdefault("file_path", "")
