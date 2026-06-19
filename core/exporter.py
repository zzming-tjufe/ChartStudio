"""图表导出 — PNG / SVG / PDF。"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Optional, Union

ExportFormat = Literal["png", "svg", "pdf"]


def _sanitize_filename_part(text: str, max_len: int = 40) -> str:
    s = re.sub(r'[<>:"/\\|?*\s]+', "", str(text).strip())
    return (s[:max_len] if s else "chart")


def build_export_basename(
    config: dict,
    *,
    project_name: str = "",
    project_root_name: str = "",
) -> str:
    """默认导出文件名基底：优先图表标题，其次项目名/文件夹名。"""
    chart = config.get("chart", {}) if isinstance(config.get("chart"), dict) else {}
    title = str(chart.get("title", "") or "").strip()
    if title:
        return _sanitize_filename_part(title)
    if project_name.strip():
        return _sanitize_filename_part(project_name)
    if project_root_name.strip():
        return _sanitize_filename_part(project_root_name)
    return "chart"


def build_export_filename(
    config: dict,
    fmt: ExportFormat,
    *,
    project_name: str = "",
    project_root_name: str = "",
    include_timestamp: bool = True,
) -> str:
    base = build_export_basename(
        config,
        project_name=project_name,
        project_root_name=project_root_name,
    )
    if include_timestamp:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base}_{ts}.{fmt}"
    return f"{base}.{fmt}"


def export_figure(
    fig: Any,
    output_dir: Union[str, Path],
    fmt: ExportFormat,
    filename: str | None = None,
    dpi: int | None = None,
    transparent: bool = False,
    config: Optional[dict] = None,
    project_name: str = "",
    project_root_name: str = "",
) -> Path:
    out_path = Path(output_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    if filename:
        file_path = out_path / filename
    elif config is not None:
        file_path = out_path / build_export_filename(
            config,
            fmt,
            project_name=project_name,
            project_root_name=project_root_name,
        )
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = out_path / f"chart_{ts}.{fmt}"

    save_kwargs: dict = {
        "format": fmt,
        "transparent": transparent,
    }

    bbox_mode = "fixed"
    if config is not None:
        export_cfg = config.get("export", {})
        if isinstance(export_cfg, dict):
            bbox_mode = str(export_cfg.get("bbox", "fixed") or "fixed").strip().lower()
    if bbox_mode == "tight":
        save_kwargs["bbox_inches"] = "tight"
    if fmt == "png":
        save_kwargs["dpi"] = dpi or fig.get_dpi()

    fig.savefig(file_path, **save_kwargs)
    return file_path.resolve()
