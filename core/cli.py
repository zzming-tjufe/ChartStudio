"""ChartStudio 命令行 — 脱离 Streamlit 的渲染 / 校验 / 复现脚本导出。"""

from __future__ import annotations

import argparse
import sys
import textwrap
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from core.config_loader import load_yaml
from core.config_migrate import normalize_config
from core.config_validator import validate_config_for_save
from core.exporter import export_figure
from core.render_service import render_chart_from_config, render_chart_from_file


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _cmd_render(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    suffix = out_path.suffix.lower().lstrip(".")
    if suffix not in ("png", "svg", "pdf"):
        print(f"不支持的输出格式：{suffix}，请使用 .png / .svg / .pdf", file=sys.stderr)
        return 1

    try:
        fig = render_chart_from_file(config_path, template_id=args.template)
        if fig is None:
            print("渲染失败：draw_chart 未返回 Figure", file=sys.stderr)
            return 1

        config = load_yaml(config_path)
        config["_project_root"] = str(config_path.parent)
        normalized, _ = normalize_config(config, template_id=args.template or config.get("template_id", ""))

        dpi = None
        transparent = False
        export_cfg = normalized.get("export", {})
        if isinstance(export_cfg, dict):
            try:
                dpi = int(export_cfg.get("dpi", 150))
            except (TypeError, ValueError):
                dpi = 150
            transparent = bool(export_cfg.get("transparent", False))

        saved = export_figure(
            fig,
            out_path.parent,
            suffix,  # type: ignore[arg-type]
            filename=out_path.name,
            dpi=dpi,
            transparent=transparent,
            config=normalized,
        )
        plt.close(fig)
        print(f"已保存：{saved}")
        return 0
    except Exception as exc:
        print(f"渲染失败：{exc}", file=sys.stderr)
        return 1


def _cmd_check(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    try:
        config = load_yaml(config_path)
        config["_project_root"] = str(config_path.parent)
        template_id = args.template or config.get("template_id", "")
        normalized, notes = normalize_config(config, template_id=template_id)

        def _probe(cfg: dict):
            return render_chart_from_config(
                cfg,
                template_id=template_id,
                project_root=config_path.parent,
            )

        issues = validate_config_for_save(
            normalized,
            template_id=template_id,
            render_probe=_probe,
        )

        if notes:
            print("迁移说明：")
            for note in notes:
                print(f"  - {note}")

        if not issues:
            print("校验通过，未发现 warn/error。")
            return 0

        has_error = False
        for item in issues:
            prefix = "ERROR" if item.level == "error" else "WARN"
            print(f"[{prefix}] {item.field}: {item.message}")
            if item.level == "error":
                has_error = True
        return 1 if has_error else 0
    except Exception as exc:
        print(f"校验失败：{exc}", file=sys.stderr)
        return 1


def _cmd_export_code(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    template_id = args.template or ""
    repo = str(_repo_root())

    script = textwrap.dedent(
        f'''\
        """ChartStudio 复现脚本 — 由 export-code 生成。"""
        from __future__ import annotations

        import os
        import sys
        from pathlib import Path

        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        PROJECT_ROOT = Path(__file__).resolve().parent
        CONFIG_PATH = PROJECT_ROOT / {config_path.name!r}
        TEMPLATE_ID = {template_id!r}
        DEFAULT_CHARTSTUDIO_ROOT = Path({repo!r})


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

            export_cfg = normalized.get("export", {{}})
            dpi = int(export_cfg.get("dpi", 150)) if isinstance(export_cfg, dict) else 150
            transparent = bool(export_cfg.get("transparent", False)) if isinstance(export_cfg, dict) else False
            out_dir = PROJECT_ROOT / "output"
            saved = export_figure(
                fig,
                out_dir,
                "png",
                dpi=dpi,
                transparent=transparent,
                config=normalized,
            )
            plt.close(fig)
            print(f"已导出：{{saved}}")


        if __name__ == "__main__":
            main()
        '''
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(script, encoding="utf-8")
    print(f"已生成复现脚本：{out_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    repo = _repo_root()
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))

    parser = argparse.ArgumentParser(prog="python -m core.cli", description="ChartStudio CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_render = sub.add_parser("render", help="渲染 chart_config.yaml 到图片")
    p_render.add_argument("config", help="chart_config.yaml 路径")
    p_render.add_argument("--template", default=None, help="模板 ID（无同目录 chart_core.py 时使用）")
    p_render.add_argument("--out", required=True, help="输出文件路径（.png/.svg/.pdf）")
    p_render.set_defaults(func=_cmd_render)

    p_check = sub.add_parser("check", help="校验配置文件")
    p_check.add_argument("config", help="chart_config.yaml 路径")
    p_check.add_argument("--template", default=None, help="模板 ID")
    p_check.set_defaults(func=_cmd_check)

    p_code = sub.add_parser("export-code", help="导出复现脚本")
    p_code.add_argument("config", help="chart_config.yaml 路径")
    p_code.add_argument("--template", default=None, help="模板 ID")
    p_code.add_argument("--out", required=True, help="输出 .py 脚本路径")
    p_code.set_defaults(func=_cmd_export_code)

    args = parser.parse_args(argv)
    with warnings.catch_warnings(record=False):
        return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
