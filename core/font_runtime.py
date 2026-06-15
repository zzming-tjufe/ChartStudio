"""
Matplotlib 字体运行时 — 解析配置、回退与 FontProperties 应用。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties, fontManager

from core.system_fonts import (
    PREFERRED_EN,
    PREFERRED_NUM,
    PREFERRED_ZH,
    ensure_font_defaults,
    resolve_font_path_by_name,
    resolve_font_with_priority,
)

FONT_FALLBACK_MESSAGE = "原字体不可用，已使用默认字体"
INTERNAL_WARNING_KEY = "_font_fallback_warning"


@dataclass
class ResolvedFont:
    name: str
    path: Optional[Path]
    used_fallback: bool


@dataclass
class FontBundle:
    zh: ResolvedFont
    en: ResolvedFont
    num: ResolvedFont

    def fp(self, role: str, size: Optional[float] = None) -> FontProperties:
        resolved = {"zh": self.zh, "en": self.en, "num": self.num}[role]
        if resolved.path and resolved.path.is_file():
            return FontProperties(fname=str(resolved.path), size=size)
        return FontProperties(family="sans-serif", size=size)


def _project_root(config: Dict[str, Any]) -> Path:
    return Path(config.get("_project_root", "."))


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


def _resolve_role(
    font_cfg: Dict[str, Any],
    role: str,
    priority: list[str],
    project_root: Path,
    *,
    path_override: str = "",
) -> ResolvedFont:
    name_key = f"{role}_name"
    path_key = f"{role}_path"
    configured_name = str(font_cfg.get(name_key, "") or "")
    configured_path = str(font_cfg.get(path_key, "") or "")
    if role == "zh" and path_override:
        configured_path = path_override

    # 下拉框名称优先：避免 zh_name 已改但 zh_path 仍是旧值
    if configured_name:
        by_name = resolve_font_path_by_name(configured_name)
        if by_name:
            path = Path(by_name)
            if path.is_file():
                return ResolvedFont(configured_name, path.resolve(), False)

    disk_path = resolve_path_on_disk(configured_path, project_root)
    if disk_path:
        return ResolvedFont(configured_name or disk_path.stem, disk_path, False)

    fallback_path = resolve_font_with_priority(configured_name, priority)
    if fallback_path:
        path = Path(fallback_path)
        if path.is_file():
            display = configured_name or path.stem
            return ResolvedFont(display, path.resolve(), True)

    return ResolvedFont("sans-serif", None, True)


def prepare_chart_fonts(config: Dict[str, Any]) -> FontBundle:
    """解析字体配置，注册字体文件，并在需要时写入运行时警告键。"""
    font_cfg = config.setdefault("font", {})
    ensure_font_defaults(font_cfg)
    root = _project_root(config)

    legacy_override = str(font_cfg.get("file_path", "") or "")
    bundle = FontBundle(
        zh=_resolve_role(font_cfg, "zh", PREFERRED_ZH, root, path_override=legacy_override),
        en=_resolve_role(font_cfg, "en", PREFERRED_EN, root),
        num=_resolve_role(font_cfg, "num", PREFERRED_NUM, root),
    )

    had_fallback = any(item.used_fallback for item in (bundle.zh, bundle.en, bundle.num))
    for item in (bundle.zh, bundle.en, bundle.num):
        if item.path and item.path.is_file():
            try:
                fontManager.addfont(str(item.path))
            except (OSError, ValueError, RuntimeError):
                had_fallback = True

    plt.rcParams["axes.unicode_minus"] = False
    primary = bundle.zh.path or bundle.en.path or bundle.num.path
    if primary and primary.is_file():
        plt.rcParams["font.family"] = FontProperties(fname=str(primary)).get_name()
    else:
        plt.rcParams["font.family"] = "sans-serif"

    if had_fallback:
        config[INTERNAL_WARNING_KEY] = FONT_FALLBACK_MESSAGE
    else:
        config.pop(INTERNAL_WARNING_KEY, None)

    return bundle


def pop_font_fallback_warning(config: Dict[str, Any]) -> Optional[str]:
    return config.pop(INTERNAL_WARNING_KEY, None)


def _tick_fontproperties(label_text: str, bundle: FontBundle, tick_size: float) -> FontProperties:
    text = str(label_text)
    if any("\u4e00" <= ch <= "\u9fff" for ch in text):
        return bundle.fp("zh", tick_size)
    stripped = text.strip().replace(".", "").replace("-", "").replace(",", "")
    if stripped.isdigit():
        return bundle.fp("num", tick_size)
    if any(ch.isalpha() for ch in text):
        return bundle.fp("en", tick_size)
    return bundle.fp("num", tick_size)


def apply_chart_fonts(fig, bundle: FontBundle, font_cfg: Dict[str, Any]) -> None:
    """将 FontProperties 应用到标题、轴标签、刻度、图例与注释。"""
    title_size = float(font_cfg.get("title_size", 16))
    label_size = float(font_cfg.get("label_size", 12))
    tick_size = float(font_cfg.get("tick_size", 10))
    legend_size = float(font_cfg.get("legend_size", 10))

    for ax in fig.get_axes():
        if ax.title:
            ax.title.set_fontproperties(bundle.fp("zh", title_size))
        xlabel = ax.xaxis.get_label()
        ylabel = ax.yaxis.get_label()
        if xlabel:
            xlabel.set_fontproperties(bundle.fp("zh", label_size))
        if ylabel:
            ylabel.set_fontproperties(bundle.fp("zh", label_size))

        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(_tick_fontproperties(label.get_text(), bundle, tick_size))

        legend = ax.get_legend()
        if legend:
            for text in legend.get_texts():
                text.set_fontproperties(bundle.fp("zh", legend_size))

        for text in ax.texts:
            text.set_fontproperties(bundle.fp("num", tick_size))

        for child in ax.get_children():
            if child.__class__.__name__ == "Annotation":
                child.set_fontproperties(bundle.fp("num", tick_size))
