"""
配置快照 — 列出、恢复、对比、删除 configs/ 下的快照。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.config_loader import load_yaml, save_yaml
from core.diff_utils import compare_configs


@dataclass
class SnapshotInfo:
    path: Path
    name: str
    mtime: float

    @property
    def mtime_label(self) -> str:
        return datetime.fromtimestamp(self.mtime).strftime("%Y-%m-%d %H:%M:%S")


def list_snapshots(project_root: Path) -> List[SnapshotInfo]:
    configs_dir = project_root / "configs"
    if not configs_dir.is_dir():
        return []
    items: List[SnapshotInfo] = []
    for p in sorted(configs_dir.glob("chart_config_*.yaml"), key=lambda x: x.stat().st_mtime,reverse=True):
        items.append(SnapshotInfo(path=p, name=p.name, mtime=p.stat().st_mtime))
    return items


def load_snapshot(path: Path) -> Dict[str, Any]:
    return load_yaml(path)


def delete_snapshot(path: Path) -> None:
    if path.is_file():
        path.unlink()


def compare_snapshot_with_current(
    snapshot: Dict[str, Any],
    current: Dict[str, Any],
) -> List[str]:
    return compare_configs(snapshot, current, human_readable=True)


def restore_snapshot_to_file(project_root: Path, snapshot_path: Path) -> Path:
    """将快照内容写回主 chart_config.yaml（不自动改 session）。"""
    target = project_root / "chart_config.yaml"
    data = load_snapshot(snapshot_path)
    save_yaml(target, data)
    return target
