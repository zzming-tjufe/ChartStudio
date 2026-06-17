"""项目打包 — 将核心文件与资源目录打包为 zip。"""

from __future__ import annotations

import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

CORE_FILES = ("chart_config.yaml", "chart_core.py", "chart_project.yaml")
RESOURCE_DIRS = ("data", "fonts", "configs")


def _iter_package_files(project_root: Path) -> Iterable[Path]:
    for name in CORE_FILES:
        p = project_root / name
        if p.is_file():
            yield p
    for dirname in RESOURCE_DIRS:
        d = project_root / dirname
        if d.is_dir():
            for f in d.rglob("*"):
                if f.is_file():
                    yield f


def build_project_zip(
    project_root: Path,
    *,
    output_dir: Path | None = None,
) -> Path:
    """打包项目，默认输出到 output/ 目录。"""
    root = project_root.resolve()
    out_dir = (output_dir or root / "output").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"{root.name}_package_{ts}.zip"
    zip_path = out_dir / zip_name

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in _iter_package_files(root):
            arcname = file_path.relative_to(root).as_posix()
            zf.write(file_path, arcname)

    return zip_path
