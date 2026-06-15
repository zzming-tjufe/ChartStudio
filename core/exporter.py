"""图表导出 — PNG / SVG / PDF。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Union

ExportFormat = Literal["png", "svg", "pdf"]


def _default_filename(base_name: str, fmt: ExportFormat) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_base = base_name.replace(" ", "_")
    return f"{safe_base}_{timestamp}.{fmt}"


def export_figure(
    fig: Any,
    output_dir: Union[str, Path],
    fmt: ExportFormat,
    filename: str | None = None,
    dpi: int | None = None,
    transparent: bool = False,
) -> Path:
    out_path = Path(output_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    if filename:
        file_path = out_path / filename
    else:
        file_path = out_path / _default_filename("chart", fmt)

    save_kwargs: dict = {
        "format": fmt,
        "bbox_inches": "tight",
        "transparent": transparent,
    }
    if fmt == "png":
        save_kwargs["dpi"] = dpi or fig.get_dpi()

    fig.savefig(file_path, **save_kwargs)
    return file_path
