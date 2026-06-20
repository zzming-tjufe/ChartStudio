"""ChartStudio 复现脚本 — 由 export-code 生成。

默认导出 SVG；生成时可指定 --format svg/pdf。
也可修改下方 EXPORT_FORMAT 常量。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / 'chart_config.yaml'
TEMPLATE_ID = 'line_chart_basic'
EXPORT_FORMAT = 'svg'
DEFAULT_CHARTSTUDIO_ROOT = Path('D:\\zzmin\\Desktop\\ChartStudio')


def _setup_import_path() -> None:
    env_root = os.environ.get("CHARTSTUDIO_ROOT", "").strip()
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.append(DEFAULT_CHARTSTUDIO_ROOT)
    candidates.extend(PROJECT_ROOT.parents)
    for candidate in candidates:
        if (candidate / "core" / "render_service.py").is_file():
            root = str(candidate.resolve())
            if root not in sys.path:
                sys.path.insert(0, root)
            return
    raise RuntimeError(
        "找不到 ChartStudio core 模块。请设置 CHARTSTUDIO_ROOT 环境变量，"
        "或在 ChartStudio 仓库内运行此脚本。"
    )


def main() -> None:
    _setup_import_path()
    from core.config_loader import load_yaml
    from core.config_migrate import normalize_config
    from core.exporter import export_figure
    from core.render_service import render_chart_from_config, resolve_chart_core_path

    config = load_yaml(CONFIG_PATH)
    config["_project_root"] = str(PROJECT_ROOT)
    tid = TEMPLATE_ID or config.get("template_id", "")
    normalized, _ = normalize_config(config, template_id=tid)
    core_path = resolve_chart_core_path(PROJECT_ROOT, tid)
    fig = render_chart_from_config(
        normalized,
        template_id=tid,
        core_path=core_path,
        project_root=PROJECT_ROOT,
    )
    if fig is None:
        raise RuntimeError("draw_chart 未返回 Figure")

    export_cfg = normalized.get("export", {})
    dpi = int(export_cfg.get("dpi", 150)) if isinstance(export_cfg, dict) else 150
    transparent = bool(export_cfg.get("transparent", False)) if isinstance(export_cfg, dict) else False
    out_dir = PROJECT_ROOT / "output"
    saved = export_figure(
        fig,
        out_dir,
        EXPORT_FORMAT,
        dpi=dpi,
        transparent=transparent,
        config=normalized,
    )
    plt.close(fig)
    print(f"已导出：{saved}")


if __name__ == "__main__":
    main()
