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

from core.cli_paths import (
    default_render_output,
    default_script_output,
    resolve_output_format,
    resolve_project_config,
)
from core.config_loader import load_yaml
from core.config_migrate import normalize_config
from core.config_validator import validate_config_for_save
from core.exporter import export_figure
from core.render_service import render_chart_from_config, render_chart_from_file

_SUBCOMMANDS = frozenset({"render", "check", "script", "export-code", "validate", "help"})


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _ensure_repo_on_path() -> None:
    repo = _repo_root()
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))


def _normalize_argv(argv: list[str]) -> list[str]:
    """无子命令时默认 render，例如：chartstudio .  →  render ."""
    if not argv:
        return ["render", "."]
    if argv[0] in _SUBCOMMANDS or argv[0].startswith("-"):
        return argv
    return ["render", *argv]


def _resolve_config_arg(path: str) -> Path:
    try:
        return resolve_project_config(path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


def _cmd_render(args: argparse.Namespace) -> int:
    config_path = _resolve_config_arg(args.config)
    try:
        fmt, explicit_out = resolve_output_format(
            out_path=Path(args.out).expanduser().resolve() if args.out else None,
            format_arg=args.format,
            default="png",
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    out_path = explicit_out if explicit_out is not None else default_render_output(config_path, fmt)

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
            fmt,  # type: ignore[arg-type]
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
    config_path = _resolve_config_arg(args.config)
    try:
        config = load_yaml(config_path)
        config["_project_root"] = str(config_path.parent)
        template_id = args.template or config.get("template_id", "")
        normalized, notes = normalize_config(config, template_id=template_id)

        def _probe(cfg: dict):
            return render_chart_from_config(cfg, template_id=template_id)

        issues = validate_config_for_save(
            normalized,
            template_id=template_id,
            render_probe=_probe,
        )

        errors = [i for i in issues if i.level == "error"]
        warns = [i for i in issues if i.level == "warn"]

        if not args.quiet:
            if notes:
                print("迁移说明：")
                for note in notes:
                    print(f"  - {note}")
            if not issues:
                print("校验通过，未发现 warn/error。")
            else:
                for item in issues:
                    prefix = "ERROR" if item.level == "error" else "WARN"
                    print(f"[{prefix}] {item.field}: {item.message}")
        elif not issues:
            print("ok")
        else:
            print(f"{len(errors)} error(s), {len(warns)} warn(s)")

        return 1 if errors else 0
    except Exception as exc:
        print(f"校验失败：{exc}", file=sys.stderr)
        return 1


def _cmd_export_code(args: argparse.Namespace) -> int:
    config_path = _resolve_config_arg(args.config)
    out_path = (
        Path(args.out).expanduser().resolve()
        if args.out
        else default_script_output(config_path)
    )
    template_id = args.template or ""
    try:
        export_format, _ = resolve_output_format(out_path=None, format_arg=args.format, default="png")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    repo = str(_repo_root())

    script = textwrap.dedent(
        f'''\
        """ChartStudio 复现脚本 — 由 chartstudio script 生成。

        默认导出 {export_format.upper()}；可修改下方 EXPORT_FORMAT 常量。
        """
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
        EXPORT_FORMAT = {export_format!r}
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
                EXPORT_FORMAT,
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


def _build_parser(prog: str = "chartstudio") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="ChartStudio CLI — 渲染 / 校验 / 导出复现脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            示例：
              chartstudio .                    # 渲染当前目录 → output/chart.png
              chartstudio render . -f svg      # 渲染为 SVG
              chartstudio check examples/v2_annotations_acceptance
              chartstudio script .             # 生成 reproduce.py
            """
        ),
    )
    sub = parser.add_subparsers(dest="command")

    def _add_target(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "config",
            nargs="?",
            default=".",
            help="项目目录或 chart_config.yaml（默认当前目录）",
        )
        p.add_argument("-t", "--template", default=None, help="模板 ID（可选）")

    p_render = sub.add_parser("render", help="渲染 chart_config.yaml 到图片")
    _add_target(p_render)
    p_render.add_argument("-o", "--out", default=None, help="输出文件（默认 项目/output/chart.png）")
    p_render.add_argument(
        "-f",
        "--format",
        default=None,
        choices=("png", "svg", "pdf"),
        help="输出格式（与 -o 二选一或组合；默认 png）",
    )
    p_render.set_defaults(func=_cmd_render)

    p_check = sub.add_parser("check", aliases=["validate"], help="校验配置文件")
    _add_target(p_check)
    p_check.add_argument("-q", "--quiet", action="store_true", help="仅输出摘要")
    p_check.set_defaults(func=_cmd_check)

    p_script = sub.add_parser(
        "script",
        aliases=["export-code"],
        help="导出复现脚本 reproduce.py",
    )
    _add_target(p_script)
    p_script.add_argument("-o", "--out", default=None, help="脚本路径（默认 项目/reproduce.py）")
    p_script.add_argument(
        "-f",
        "--format",
        default="png",
        choices=("png", "svg", "pdf"),
        help="脚本内默认导出格式（默认 png）",
    )
    p_script.set_defaults(func=_cmd_export_code)

    return parser


def main(argv: list[str] | None = None) -> int:
    _ensure_repo_on_path()
    raw = list(argv if argv is not None else sys.argv[1:])

    prog = "chartstudio"
    if Path(sys.argv[0]).name in ("cli.py", "cli"):
        prog = "python -m core.cli"

    parser = _build_parser(prog=prog)

    if raw in ([], ["-h"], ["--help"]):
        parser.print_help()
        return 0

    normalized = _normalize_argv(raw)
    args = parser.parse_args(normalized)

    if not getattr(args, "func", None):
        parser.print_help()
        return 0

    with warnings.catch_warnings(record=False):
        return args.func(args)


def main_entry() -> None:
    """console_scripts 入口（pip install -e . 后可用 chartstudio / cs）。"""
    raise SystemExit(main())


if __name__ == "__main__":
    raise SystemExit(main())
