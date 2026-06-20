"""CLI 路径解析 — 项目目录 / chart_config.yaml / 默认输出。"""

from __future__ import annotations

import re
from pathlib import Path

CONFIG_FILENAME = "chart_config.yaml"
EXPORT_FORMATS = frozenset({"png", "svg", "pdf"})


def resolve_project_config(path: str | Path = ".") -> Path:
    """
    解析项目配置路径。

    - 目录 → 查找目录内 chart_config.yaml
    - 文件 → 直接使用（通常为 chart_config.yaml）
    """
    raw = Path(path).expanduser()
    if not raw.is_absolute():
        raw = raw.resolve()
    else:
        raw = raw.resolve()

    if raw.is_file():
        return raw

    if raw.is_dir():
        candidate = raw / CONFIG_FILENAME
        if candidate.is_file():
            return candidate.resolve()
        raise FileNotFoundError(f"目录中未找到 {CONFIG_FILENAME}：{raw}")

    raise FileNotFoundError(f"路径不存在：{raw}")


def project_root_of(config_path: Path) -> Path:
    return config_path.resolve().parent


def _safe_stem(text: str, fallback: str = "chart") -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", str(text or "").strip())
    cleaned = re.sub(r"\s+", "_", cleaned).strip("._")
    return cleaned[:80] if cleaned else fallback


def default_render_output(config_path: Path, fmt: str = "png") -> Path:
    """默认输出：{项目目录}/output/{名称}.{fmt}"""
    fmt = fmt.lower().lstrip(".")
    if fmt not in EXPORT_FORMATS:
        fmt = "png"

    root = project_root_of(config_path)
    out_dir = root / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = "chart"
    try:
        from core.config_loader import load_yaml

        cfg = load_yaml(config_path)
        chart = cfg.get("chart", {}) if isinstance(cfg.get("chart"), dict) else {}
        title = str(chart.get("title", "") or "").strip()
        if title:
            stem = _safe_stem(title)
    except Exception:
        pass

    return out_dir / f"{stem}.{fmt}"


def default_script_output(config_path: Path) -> Path:
    return project_root_of(config_path) / "reproduce.py"


def resolve_output_format(
    *,
    out_path: Path | None,
    format_arg: str | None,
    default: str = "png",
) -> tuple[str, Path | None]:
    """
    从 -f / -o 推断导出格式；若 out_path 为 None 则仅返回格式。
    """
    fmt = (format_arg or default).lower().lstrip(".")
    if out_path is not None and out_path.suffix:
        suffix = out_path.suffix.lower().lstrip(".")
        if suffix in EXPORT_FORMATS:
            fmt = suffix
    if fmt not in EXPORT_FORMATS:
        raise ValueError(f"不支持的格式：{fmt}，请使用 png / svg / pdf")
    return fmt, out_path
