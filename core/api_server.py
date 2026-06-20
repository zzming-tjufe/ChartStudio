"""ChartStudio 轻量 API — React Annotation Editor 原型后端。"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.config_loader import load_yaml, save_yaml
from core.config_migrate import normalize_config
from core.config_validator import has_blocking_errors, validate_config_for_save
from core.layout import DEFAULT_LAYOUT
from core.project_manager import validate_project
from core.project_path_input import (
    _pick_config_file_dialog,
    _pick_folder_dialog,
    _project_root_from_file,
    assess_open_project_path,
    validate_dropped_project_file,
)
from core.render_service import render_chart_from_config

app = FastAPI(title="ChartStudio API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OpenConfigRequest(BaseModel):
    config_path: str


class AssessPathRequest(BaseModel):
    path: str


class PickDialogRequest(BaseModel):
    title: Optional[str] = None


class ValidateDropRequest(BaseModel):
    filename: str
    content: str


class RenderRequest(BaseModel):
    config_path: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class SaveConfigRequest(BaseModel):
    config_path: str
    config: Dict[str, Any]


class CheckRequest(BaseModel):
    config: Dict[str, Any]
    template_id: Optional[str] = None


class ValidationIssueOut(BaseModel):
    level: str
    field: str
    message: str


def _resolve_project_root(raw_path: str) -> Path:
    text = raw_path.strip()
    if not text:
        raise HTTPException(status_code=400, detail="请先输入、浏览或拖入配置文件以定位项目文件夹")
    path = Path(text).expanduser().resolve()
    if path.is_file():
        return path.parent
    if path.is_dir():
        return path
    raise HTTPException(status_code=404, detail=f"找不到路径：{path}")


def _resolve_config_and_root(
    config_path: Optional[str],
    config: Optional[Dict[str, Any]],
) -> tuple[Dict[str, Any], Path, str]:
    if config_path:
        project_root = _resolve_project_root(config_path)
        path = project_root / "chart_config.yaml"
        if not path.is_file():
            raise HTTPException(status_code=404, detail=f"缺少必需文件：chart_config.yaml")
        raw = load_yaml(path)
        raw["_project_root"] = str(project_root)
    elif config is not None:
        raw = dict(config)
        root_str = str(raw.get("_project_root", "") or "")
        if not root_str:
            raise HTTPException(status_code=400, detail="config 缺少 _project_root 或需提供 config_path")
        project_root = Path(root_str).resolve()
    else:
        raise HTTPException(status_code=400, detail="需提供 config_path 或 config")

    template_id = str(raw.get("template_id", "") or "line_chart_basic")
    normalized, _ = normalize_config(raw, template_id=template_id)
    normalized["_project_root"] = str(project_root)
    return normalized, project_root, template_id


def _figure_pixel_size(config: Dict[str, Any]) -> tuple[float, float, int]:
    figure = config.get("figure", {}) if isinstance(config.get("figure"), dict) else {}
    export = config.get("export", {}) if isinstance(config.get("export"), dict) else {}
    width_in = float(figure.get("width", 10.0))
    height_in = float(figure.get("height", 6.0))
    dpi = int(export.get("dpi", 150))
    return width_in * dpi, height_in * dpi, dpi


def _data_bounds(config: Dict[str, Any]) -> Optional[Dict[str, float]]:
    axes = config.get("axes", {}) if isinstance(config.get("axes"), dict) else {}
    xlim = axes.get("xlim")
    ylim = axes.get("ylim")
    if isinstance(xlim, (list, tuple)) and len(xlim) >= 2:
        x_min, x_max = float(xlim[0]), float(xlim[1])
    else:
        x_min = x_max = None
    if isinstance(ylim, (list, tuple)) and len(ylim) >= 2:
        y_min, y_max = float(ylim[0]), float(ylim[1])
    else:
        y_min = y_max = None

    data = config.get("data", {})
    if isinstance(data, dict):
        xs = data.get("x")
        if isinstance(xs, list) and xs:
            try:
                x_vals = [float(v) for v in xs]
                if x_min is None:
                    x_min, x_max = min(x_vals), max(x_vals)
            except (TypeError, ValueError):
                pass
        y_vals: List[float] = []
        for key, val in data.items():
            if key == "x" or not isinstance(val, list):
                continue
            for v in val:
                try:
                    y_vals.append(float(v))
                except (TypeError, ValueError):
                    pass
        if y_vals and y_min is None:
            y_min, y_max = min(y_vals), max(y_vals)

    if x_min is None or x_max is None or y_min is None or y_max is None:
        return None
    if x_max == x_min:
        x_max = x_min + 1.0
    if y_max == y_min:
        y_max = y_min + 1.0
    return {"xMin": x_min, "xMax": x_max, "yMin": y_min, "yMax": y_max}


def _axes_screen_rect(config: Dict[str, Any]) -> Dict[str, Any]:
    layout = config.get("layout", {})
    if not isinstance(layout, dict):
        layout = {}
    left = float(layout.get("left", DEFAULT_LAYOUT["left"]))
    right = float(layout.get("right", DEFAULT_LAYOUT["right"]))
    bottom = float(layout.get("bottom", DEFAULT_LAYOUT["bottom"]))
    top = float(layout.get("top", DEFAULT_LAYOUT["top"]))
    width_px, height_px, dpi = _figure_pixel_size(config)
    axes_left = left * width_px
    axes_width = (right - left) * width_px
    axes_top = height_px * (1.0 - top)
    axes_height = height_px * (top - bottom)
    return {
        "left": axes_left,
        "top": axes_top,
        "width": axes_width,
        "height": axes_height,
        "canvasWidth": width_px,
        "canvasHeight": height_px,
        "dpi": dpi,
        "layout": {
            "left": left,
            "right": right,
            "bottom": bottom,
            "top": top,
            "use_tight_layout": bool(layout.get("use_tight_layout", False)),
        },
    }


def _render_meta(config: Dict[str, Any]) -> Dict[str, Any]:
    meta = _axes_screen_rect(config)
    bounds = _data_bounds(config)
    if bounds:
        meta["dataBounds"] = bounds
    return meta


def _figure_to_svg(fig) -> str:
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches=None, pad_inches=0)
    plt.close(fig)
    return buf.getvalue()


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/assess-open-path")
def assess_path(body: AssessPathRequest) -> Dict[str, str]:
    status, message = assess_open_project_path(body.path)
    return {"status": status, "message": message}


@app.post("/api/pick-folder")
def pick_folder(body: PickDialogRequest) -> Dict[str, Optional[str]]:
    title = body.title or "选择 ChartStudio 项目文件夹"
    picked = _pick_folder_dialog(title)
    return {"path": picked}


@app.post("/api/pick-config-file")
def pick_config_file(body: PickDialogRequest) -> Dict[str, Optional[str]]:
    title = body.title or "选择 chart_config.yaml 以定位项目"
    picked = _pick_config_file_dialog(title)
    if not picked:
        return {"path": None, "project_root": None}
    root = _project_root_from_file(picked)
    return {"path": picked, "project_root": root}


@app.post("/api/validate-drop")
def validate_drop(body: ValidateDropRequest) -> Dict[str, Any]:
    raw = body.content.encode("utf-8")
    ok, message = validate_dropped_project_file(body.filename, raw)
    return {"ok": ok, "message": message}


@app.post("/api/open-config")
def open_config(body: OpenConfigRequest) -> Dict[str, Any]:
    project_root = _resolve_project_root(body.config_path)
    ok, msg, info = validate_project(project_root)
    if not ok or info is None:
        raise HTTPException(status_code=400, detail=msg)

    config, _, template_id = _resolve_config_and_root(str(project_root), None)
    return {
        "config": config,
        "config_path": str(info.config_path),
        "project_root": str(info.root),
        "template_id": template_id,
        "project_name": info.display_name,
        "template_name": info.template_name,
        "message": msg,
        "meta": _render_meta(config),
    }


@app.post("/api/render")
def render_chart(body: RenderRequest) -> Dict[str, Any]:
    config, project_root, template_id = _resolve_config_and_root(body.config_path, body.config)
    try:
        fig = render_chart_from_config(
            config,
            template_id=template_id,
            project_root=project_root,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"渲染失败：{exc}") from exc

    if fig is None:
        raise HTTPException(status_code=500, detail="draw_chart 未返回 Figure")

    svg = _figure_to_svg(fig)
    meta = _render_meta(config)
    figure = config.get("figure", {}) if isinstance(config.get("figure"), dict) else {}
    return {
        "svg": svg,
        "meta": meta,
        "figure": {
            "width": float(figure.get("width", 10.0)),
            "height": float(figure.get("height", 6.0)),
        },
    }


@app.post("/api/save-config")
def save_config(body: SaveConfigRequest) -> Dict[str, Any]:
    path = Path(body.config_path).expanduser().resolve()
    config = dict(body.config)
    config["_project_root"] = str(path.parent)
    template_id = str(config.get("template_id", "") or "line_chart_basic")
    normalized, notes = normalize_config(config, template_id=template_id)
    normalized["_project_root"] = str(path.parent)

    issues = validate_config_for_save(normalized, template_id=template_id)
    if has_blocking_errors(issues):
        raise HTTPException(
            status_code=400,
            detail={
                "message": "配置校验未通过",
                "issues": [
                    {"level": i.level, "field": i.field, "message": i.message} for i in issues
                ],
            },
        )

    save_yaml(path, normalized)
    return {
        "saved": str(path),
        "migration_notes": notes,
        "issues": [
            {"level": i.level, "field": i.field, "message": i.message}
            for i in issues
            if i.level == "warn"
        ],
    }


@app.post("/api/check")
def check_config(body: CheckRequest) -> Dict[str, Any]:
    config = dict(body.config)
    template_id = body.template_id or str(config.get("template_id", "") or "line_chart_basic")
    normalized, notes = normalize_config(config, template_id=template_id)
    issues = validate_config_for_save(normalized, template_id=template_id)
    return {
        "issues": [
            ValidationIssueOut(level=i.level, field=i.field, message=i.message) for i in issues
        ],
        "migration_notes": notes,
        "blocking": has_blocking_errors(issues),
    }
