from __future__ import annotations

import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

from emotion_types import LABEL_ORDER_INDEX, MAX_DEGRADATION_REASONS


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return low
    if not math.isfinite(number):
        return low
    return max(low, min(high, number))


def safe_float(value: Any, default: float = 0.0, diagnostics: dict[str, Any] | None = None, reason: str = "number_invalid") -> float:
    if value is None:
        return default
    if isinstance(value, str) and not value.strip():
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        if diagnostics is not None:
            mark_degraded(diagnostics, reason)
        return default
    if not math.isfinite(number):
        if diagnostics is not None:
            mark_degraded(diagnostics, reason)
        return default
    return number


def safe_int(value: Any, default: int = 0, diagnostics: dict[str, Any] | None = None, reason: str = "number_invalid") -> int:
    return int(safe_float(value, float(default), diagnostics, reason))


def load_json_file(path: str | None) -> Any:
    if not path:
        return None
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"JSON input file not found: {file_path}")
    return json.loads(file_path.read_text(encoding="utf-8"))


def require_json_object(value: Any, source: str) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    value_type = type(value).__name__
    raise ValueError(f"Top-level JSON object required: {source} got {value_type}")


def dump_json(data: Any, pretty: bool) -> str:
    if pretty:
        return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            handle.write(text)
            tmp_path = Path(handle.name)
        os.replace(tmp_path, path)
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def unique_labels(labels: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for label in labels:
        if label not in seen:
            seen.add(label)
            result.append(label)
    return result


def intensity_band(score: float) -> str:
    if score >= 0.75:
        return "dominant"
    if score >= 0.55:
        return "strong"
    if score >= 0.3:
        return "present"
    return "background"


def normalized_label_set(labels: list[str]) -> set[str]:
    raw = {str(label) for label in labels if str(label).strip()}
    if not raw:
        return set()
    trimmed = {label for label in raw if label != "neutral"}
    return trimmed or raw


def label_overlap_score(labels_a: list[str], labels_b: list[str]) -> float:
    set_a = normalized_label_set(labels_a)
    set_b = normalized_label_set(labels_b)
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    return round(clamp(len(set_a & set_b) / len(set_a | set_b)), 4)


def vector_alignment_score(vector_a: dict[str, Any], vector_b: dict[str, Any], dims: tuple[str, ...]) -> float:
    if not vector_a or not vector_b:
        return 0.0
    diff = 0.0
    for dim in dims:
        diff += abs(safe_float(vector_a.get(dim), 0.0) - safe_float(vector_b.get(dim), 0.0))
    return round(clamp(1.0 - (diff / max(len(dims), 1))), 4)


def dominant_axes(vector: dict[str, Any], dims: tuple[str, ...], top_n: int = 2, floor: float = 0.32) -> set[str]:
    ranked = sorted(((dim, safe_float(vector.get(dim), 0.0)) for dim in dims), key=lambda item: item[1], reverse=True)
    picked = [dim for dim, value in ranked[:top_n] if value >= floor]
    return set(picked)


def axis_overlap_score(vector_a: dict[str, Any], vector_b: dict[str, Any], dims: tuple[str, ...]) -> float:
    axes_a = dominant_axes(vector_a, dims)
    axes_b = dominant_axes(vector_b, dims)
    if not axes_a and not axes_b:
        return 1.0
    if not axes_a or not axes_b:
        return 0.0
    return round(clamp(len(axes_a & axes_b) / len(axes_a | axes_b)), 4)


def clamp_dict(
    raw: Any,
    keys: tuple[str, ...],
    defaults: dict[str, float] | None = None,
    diagnostics: dict[str, Any] | None = None,
    reason_prefix: str = "value",
) -> dict[str, float]:
    base = {key: clamp(safe_float((defaults or {}).get(key), 0.0)) for key in keys}
    if not isinstance(raw, dict):
        return base
    for key in keys:
        if key in raw and raw[key] is not None:
            base[key] = clamp(safe_float(raw[key], base[key], diagnostics, f"{reason_prefix}.{key}_invalid"))
    return base


def mark_degraded(diagnostics: dict[str, Any], reason: str) -> None:
    reasons = diagnostics.setdefault("degradation_reasons", [])
    if reason not in reasons:
        reasons.append(reason)
    diagnostics["degraded"] = True


def as_mapping(value: Any, diagnostics: dict[str, Any], reason: str) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                mark_degraded(diagnostics, reason)
                return {}
            if isinstance(parsed, dict):
                mark_degraded(diagnostics, f"{reason}.parsed_from_json_string")
                return parsed
    mark_degraded(diagnostics, reason)
    return {}


def normalize_string_list(value: Any, diagnostics: dict[str, Any], reason: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        mark_degraded(diagnostics, reason)
        return []
    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            mark_degraded(diagnostics, f"{reason}.contains_non_string")
            continue
        text = item.strip()
        if text:
            result.append(text)
    return result


def canonicalize_labels(labels: list[str]) -> list[str]:
    ordered = unique_labels([str(label).strip() for label in labels if str(label).strip()])
    return sorted(ordered, key=lambda label: (LABEL_ORDER_INDEX.get(label, len(LABEL_ORDER_INDEX)), label))


def normalize_history(value: Any, diagnostics: dict[str, Any]) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        mark_degraded(diagnostics, "history_not_list")
        return []
    normalized: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            mark_degraded(diagnostics, f"history_item_{index}_not_mapping")
            continue
        role = item.get("role", "")
        if role is None:
            role = ""
        elif not isinstance(role, str):
            mark_degraded(diagnostics, f"history_item_{index}_role_not_string")
            role = str(role) if isinstance(role, (int, float, bool)) else ""
        text = item.get("text")
        if text is None:
            text = item.get("content")
        if text is None:
            text = ""
        elif not isinstance(text, str):
            mark_degraded(diagnostics, f"history_item_{index}_text_not_string")
            text = str(text) if isinstance(text, (int, float, bool)) else ""
        if not role and not text:
            continue
        normalized.append({
            "role": role.strip(),
            "text": text,
        })
    return normalized


def finalize_degradation_reasons(diagnostics: dict[str, Any]) -> list[str]:
    reasons = unique_labels([str(reason).strip() for reason in diagnostics.get("degradation_reasons", []) if str(reason).strip()])
    if len(reasons) > MAX_DEGRADATION_REASONS:
        overflow = len(reasons) - (MAX_DEGRADATION_REASONS - 2)
        reasons = reasons[: MAX_DEGRADATION_REASONS - 2] + ["degradation_reasons_truncated", f"...+{overflow} more"]
    diagnostics["degradation_reasons"] = reasons
    diagnostics["degraded"] = bool(reasons) or bool(diagnostics.get("degraded"))
    return reasons


def combine_named_vectors(weighted_vectors: list[tuple[dict[str, Any], float]], dims: tuple[str, ...]) -> dict[str, float]:
    """Combine partial vectors with independent per-dimension weighted averages."""
    totals = {dim: 0.0 for dim in dims}
    weight_sum = {dim: 0.0 for dim in dims}
    for vector, weight in weighted_vectors:
        if not vector or weight <= 0:
            continue
        for dim in dims:
            value = vector.get(dim)
            if value is None:
                continue
            totals[dim] += safe_float(value, 0.0) * weight
            weight_sum[dim] += weight
    result: dict[str, float] = {}
    for dim in dims:
        if weight_sum[dim] > 0:
            result[dim] = round(clamp(totals[dim] / weight_sum[dim]), 4)
        else:
            result[dim] = 0.0
    return result
