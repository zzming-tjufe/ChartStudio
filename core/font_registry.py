"""
ChartStudio 字体注册表 — 友好显示名与可复现 family/path 的单一真相源。
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from core.system_fonts import resolve_font_path_by_name

FontValue = Union[str, Dict[str, Any], None]

ROLE_FALLBACK_ORDER: Dict[str, List[str]] = {
    "zh": ["microsoft_yahei", "simhei", "simsun", "kaiti"],
    "en": ["times_new_roman", "arial", "calibri"],
    "num": ["times_new_roman", "arial", "calibri"],
}


def _windows_fonts_dir() -> Path:
    return Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"


def _path_candidates(rel_names: List[str]) -> List[str]:
    base = _windows_fonts_dir()
    out: List[str] = []
    for name in rel_names:
        out.append(str(base / name))
    return out


FONT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "microsoft_yahei": {
        "display": "微软雅黑",
        "family": "Microsoft YaHei",
        "aliases": ["微软雅黑", "Microsoft YaHei", "MicrosoftYaHei", "MS YaHei"],
        "path_candidates": _path_candidates(["msyh.ttc", "msyh.ttf", "msyhbd.ttc"]),
        "role": ["zh"],
    },
    "simsun": {
        "display": "宋体",
        "family": "SimSun",
        "aliases": ["宋体", "SimSun", "NSimSun", "新宋体"],
        "path_candidates": _path_candidates(["simsun.ttc", "simsun.ttf"]),
        "role": ["zh"],
    },
    "simhei": {
        "display": "黑体",
        "family": "SimHei",
        "aliases": ["黑体", "SimHei"],
        "path_candidates": _path_candidates(["simhei.ttf"]),
        "role": ["zh"],
    },
    "kaiti": {
        "display": "楷体",
        "family": "KaiTi",
        "aliases": ["楷体", "KaiTi", "KaiTi_GB2312"],
        "path_candidates": _path_candidates(["simkai.ttf", "kaiti.ttf"]),
        "role": ["zh"],
    },
    "fangsong": {
        "display": "仿宋",
        "family": "FangSong",
        "aliases": ["仿宋", "FangSong"],
        "path_candidates": _path_candidates(["simfang.ttf"]),
        "role": ["zh"],
    },
    "times_new_roman": {
        "display": "Times New Roman",
        "family": "Times New Roman",
        "aliases": ["Times New Roman", "TimesNewRoman", "Times"],
        "path_candidates": _path_candidates(["times.ttf", "timesbd.ttf", "timesi.ttf"]),
        "role": ["en", "num"],
    },
    "arial": {
        "display": "Arial",
        "family": "Arial",
        "aliases": ["Arial", "ArialMT"],
        "path_candidates": _path_candidates(["arial.ttf", "arialbd.ttf"]),
        "role": ["en", "num"],
    },
    "calibri": {
        "display": "Calibri",
        "family": "Calibri",
        "aliases": ["Calibri"],
        "path_candidates": _path_candidates(["calibri.ttf", "calibrib.ttf"]),
        "role": ["en", "num"],
    },
    "courier_new": {
        "display": "Courier New",
        "family": "Courier New",
        "aliases": ["Courier New", "CourierNew"],
        "path_candidates": _path_candidates(["cour.ttf", "courbd.ttf"]),
        "role": ["en", "num"],
    },
}


def _normalize_key(text: str) -> str:
    return str(text).strip().lower().replace(" ", "").replace("_", "")


def _find_registry_entry(
    needle: str,
    role: Optional[str] = None,
) -> Optional[tuple[str, Dict[str, Any]]]:
    raw = str(needle).strip()
    if not raw:
        return None
    norm = _normalize_key(raw)
    for reg_id, entry in FONT_REGISTRY.items():
        if role and role not in entry.get("role", []):
            continue
        candidates = [
            reg_id,
            entry.get("display", ""),
            entry.get("family", ""),
            *entry.get("aliases", []),
        ]
        for c in candidates:
            if not c:
                continue
            if _normalize_key(c) == norm or c == raw:
                return reg_id, entry
    if role is None:
        for reg_id, entry in FONT_REGISTRY.items():
            candidates = [
                reg_id,
                entry.get("display", ""),
                entry.get("family", ""),
                *entry.get("aliases", []),
            ]
            for c in candidates:
                if not c:
                    continue
                if _normalize_key(c) == norm or c == raw:
                    return reg_id, entry
    return None


def _first_existing_path(
    candidates: List[str],
    project_root: Optional[Path] = None,
) -> tuple[str, str]:
    """返回 (path, source)。source: system | project | empty。"""
    for raw in candidates:
        if not raw or not str(raw).strip():
            continue
        path = Path(str(raw).strip())
        if path.is_file():
            return str(path.resolve()), "system" if "Windows" in str(path) or "Fonts" in str(path) else "system"
        if project_root is not None:
            for candidate in (project_root / path, project_root / "fonts" / path.name):
                if candidate.is_file():
                    return str(candidate.resolve()), "project"
    return "", ""


def resolve_font_option(
    value: FontValue,
    role: str = "zh",
    *,
    project_root: Optional[Path] = None,
    warn: bool = True,
) -> Dict[str, Any]:
    """
    将任意字体输入规范为注册表结构。

    返回字段：registry_id, display, family, path, source, status
    status: ok | path_missing | fallback | unknown
    """
    base: Dict[str, Any] = {
        "registry_id": "",
        "display": "",
        "family": "",
        "path": "",
        "source": "",
        "status": "unknown",
    }

    incoming: Dict[str, Any] = {}
    if isinstance(value, dict):
        incoming = dict(value)
    elif isinstance(value, str) and value.strip():
        incoming = {"display": value.strip(), "family": value.strip()}

    # 已有 path 优先
    configured_path = str(incoming.get("path", "") or "").strip()
    path, source = _first_existing_path([configured_path], project_root)
    if path:
        base["path"] = path
        base["source"] = source or str(incoming.get("source", "") or "custom")

    # 从 registry_id / display / family / aliases 匹配
    lookup_keys = [
        str(incoming.get("registry_id", "") or ""),
        str(incoming.get("display", "") or ""),
        str(incoming.get("family", "") or ""),
    ]
    if isinstance(value, str):
        lookup_keys.insert(0, value.strip())

    matched: Optional[tuple[str, Dict[str, Any]]] = None
    for key in lookup_keys:
        if not key:
            continue
        found = _find_registry_entry(key, role=role)
        if found:
            matched = found
            break

    if matched:
        reg_id, entry = matched
        base["registry_id"] = reg_id
        base["display"] = str(entry.get("display", "") or incoming.get("display", "") or entry.get("family", ""))
        base["family"] = str(entry.get("family", "") or incoming.get("family", ""))
        if not base["path"]:
            path, source = _first_existing_path(entry.get("path_candidates", []), project_root)
            if path:
                base["path"] = path
                base["source"] = source or "system"
            elif warn:
                warnings.warn(
                    f"字体「{base['display']}」注册路径均不存在，path 留空",
                    stacklevel=2,
                )
        base["status"] = "ok" if base["path"] else "path_missing"
        return base

    # 非注册表字体：尝试系统 catalog
    family = str(incoming.get("family", "") or incoming.get("display", "") or (value if isinstance(value, str) else ""))
    display = str(incoming.get("display", "") or family)
    if family:
        base["display"] = display
        base["family"] = family
        if not base["path"]:
            resolved = resolve_font_path_by_name(family) or resolve_font_path_by_name(display)
            if resolved and Path(resolved).is_file():
                base["path"] = resolved
                base["source"] = "system"
                base["status"] = "ok"
            else:
                base["status"] = "path_missing"
                if warn:
                    warnings.warn(
                        f"字体「{display}」未在注册表且系统路径未找到，family={family!r}",
                        stacklevel=2,
                    )
        else:
            base["status"] = "ok"
        return base

    # registry fallback 链
    for reg_id in ROLE_FALLBACK_ORDER.get(role, []):
        entry = FONT_REGISTRY.get(reg_id)
        if not entry or role not in entry.get("role", []):
            continue
        path, source = _first_existing_path(entry.get("path_candidates", []), project_root)
        if path:
            base.update(
                {
                    "registry_id": reg_id,
                    "display": entry["display"],
                    "family": entry["family"],
                    "path": path,
                    "source": source or "system",
                    "status": "fallback",
                }
            )
            if warn:
                warnings.warn(
                    f"字体 role={role} 无法解析输入，已 fallback 到「{entry['display']}」",
                    stacklevel=2,
                )
            return base

    base["status"] = "unknown"
    return base


def registry_display_options(role: str) -> List[str]:
    """某 role 在 UI 中可选的友好显示名列表。"""
    preferred = ROLE_FALLBACK_ORDER.get(role, [])
    displays: List[str] = []
    for reg_id in preferred:
        entry = FONT_REGISTRY.get(reg_id)
        if entry and role in entry.get("role", []):
            displays.append(str(entry["display"]))
    for reg_id, entry in FONT_REGISTRY.items():
        disp = str(entry.get("display", ""))
        if role in entry.get("role", []) and disp and disp not in displays:
            displays.append(disp)
    return displays


def sync_font_role_to_legacy(font_cfg: Dict[str, Any], role: str, resolved: Dict[str, Any]) -> None:
    """写入 font[role] 对象并同步旧扁平字段（兼容）。"""
    font_cfg[role] = {
        "display": resolved.get("display", ""),
        "family": resolved.get("family", ""),
        "path": resolved.get("path", ""),
        "source": resolved.get("source", ""),
        "status": resolved.get("status", ""),
    }
    if resolved.get("registry_id"):
        font_cfg[role]["registry_id"] = resolved["registry_id"]
    name_key = f"{role}_name"
    path_key = f"{role}_path"
    font_cfg[name_key] = resolved.get("family", "") or resolved.get("display", "")
    if resolved.get("path"):
        font_cfg[path_key] = resolved["path"]


def normalize_font_roles(
    font_cfg: Dict[str, Any],
    *,
    project_root: Optional[Path] = None,
    warn: bool = False,
) -> List[str]:
    """补齐 font.zh / en / num 并同步旧字段。"""
    notes: List[str] = []
    for role in ("zh", "en", "num"):
        role_block = font_cfg.get(role)
        name_key = f"{role}_name"
        path_key = f"{role}_path"

        if isinstance(role_block, dict) and role_block:
            value: FontValue = dict(role_block)
        else:
            value = {}
            if font_cfg.get(name_key):
                value["family"] = str(font_cfg[name_key])
                value["display"] = str(font_cfg[name_key])
            if font_cfg.get(path_key):
                value["path"] = str(font_cfg[path_key])

        if role == "zh":
            legacy = str(font_cfg.get("file_path", "") or "").strip()
            if legacy and not value.get("path"):
                value["path"] = legacy
                value["source"] = "project"

        if not value:
            value = registry_display_options(role)[0] if registry_display_options(role) else ""

        before_family = ""
        if isinstance(font_cfg.get(role), dict):
            before_family = str(font_cfg[role].get("family", "") or "")

        resolved = resolve_font_option(value, role, project_root=project_root, warn=warn)
        sync_font_role_to_legacy(font_cfg, role, resolved)

        if not before_family and resolved.get("family"):
            notes.append(f"已补齐 font.{role}（{resolved.get('display')} → {resolved.get('family')}）")
        elif before_family and resolved.get("family") and before_family != resolved.get("family"):
            notes.append(
                f"font.{role}.family 已规范：{before_family} → {resolved.get('family')}"
            )

    return notes


def diagnose_font_role(
    font_cfg: Dict[str, Any],
    role: str,
    config: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """单 role 诊断行。"""
    role_label = {"zh": "中文", "en": "英文", "num": "数字"}.get(role, role)
    block = font_cfg.get(role) if isinstance(font_cfg.get(role), dict) else {}
    display = str(block.get("display", "") or "")
    family = str(block.get("family", "") or font_cfg.get(f"{role}_name", "") or "")
    path = str(block.get("path", "") or font_cfg.get(f"{role}_path", "") or "")
    status = str(block.get("status", "") or "")

    lines = [f"{role_label}字体："]
    lines.append(f"  - 显示名称：{display or '—'}")
    lines.append(f"  - 实际 family：{family or '—'}")
    lines.append(f"  - 实际路径：{path or '—'}")

    if config is not None:
        from core.font_utils import resolve_font_properties

        fp = resolve_font_properties(config, role, warn=False)
        try:
            final_path = fp.get_file() if fp else None
        except Exception:
            final_path = None
        final_family = fp.get_name() if fp else ""
        if final_path and Path(final_path).is_file():
            lines.append(f"  - 渲染结果：可用（{final_path}）")
        elif final_family:
            lines.append(f"  - 渲染结果：family fallback（{final_family}）")
        else:
            lines.append("  - 渲染结果：不可用")

    if status:
        status_map = {
            "ok": "配置完整",
            "path_missing": "路径不存在",
            "fallback": "已使用 fallback",
            "unknown": "未识别",
        }
        lines.append(f"  - 状态：{status_map.get(status, status)}")
    return lines
