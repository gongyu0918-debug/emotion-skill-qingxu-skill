#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import emotion_engine as ee


STORE_FILES = {
    "user_profile": "user_profile.json",
    "last_state": "last_state.json",
    "calibration_state": "calibration_state.json",
}


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(data: Any, pretty: bool) -> str:
    if pretty:
        return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merged[key] = merge_dict(base[key], value)
        else:
            merged[key] = value
    return merged


def load_store(store_dir: Path) -> dict[str, Any]:
    return {
        key: load_json(store_dir / filename, {})
        for key, filename in STORE_FILES.items()
    }


def build_payload(event: dict[str, Any], store: dict[str, Any]) -> dict[str, Any]:
    payload = dict(event)
    payload["user_profile"] = merge_dict(store.get("user_profile", {}), payload.get("user_profile", {}))
    if store.get("last_state") and "last_state" not in payload:
        payload["last_state"] = store["last_state"]
    if store.get("calibration_state") and "calibration_state" not in payload:
        payload["calibration_state"] = store["calibration_state"]
    return payload


def build_persisted_profile(payload: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    base_profile = dict(payload.get("user_profile") or {})
    memory_update = result["memory_update"]
    base_profile["baseline"] = memory_update["proposed_baseline"]
    base_profile["persona_traits"] = memory_update["proposed_persona_traits"]
    base_profile["affective_prior"] = memory_update["proposed_affective_prior"]
    if "timezone" not in base_profile and result["profile_state"]["timezone"]:
        base_profile["timezone"] = result["profile_state"]["timezone"]
    if "work_hours_local" not in base_profile and result["profile_state"]["work_hours_local"]:
        base_profile["work_hours_local"] = result["profile_state"]["work_hours_local"]
    return base_profile


def build_persisted_state(result: dict[str, Any]) -> dict[str, Any]:
    confirmed = result["confirmed_state"]
    return {
        "vector": confirmed["vector"],
        "emotion_vector": confirmed["emotion_vector"],
        "ttl_seconds": confirmed["ttl_seconds"],
    }


def persist_store(store_dir: Path, payload: dict[str, Any], result: dict[str, Any]) -> None:
    store_dir.mkdir(parents=True, exist_ok=True)
    (store_dir / STORE_FILES["user_profile"]).write_text(
        dump_json(build_persisted_profile(payload, result), pretty=True),
        encoding="utf-8",
    )
    (store_dir / STORE_FILES["last_state"]).write_text(
        dump_json(build_persisted_state(result), pretty=True),
        encoding="utf-8",
    )
    (store_dir / STORE_FILES["calibration_state"]).write_text(
        dump_json(result["memory_update"]["proposed_calibration_state"], pretty=True),
        encoding="utf-8",
    )


def run_event(event_path: Path, store_dir: Path, pretty: bool) -> dict[str, Any]:
    event = load_json(event_path, {})
    if not event:
        raise ValueError(f"Event payload is empty: {event_path}")
    store = load_store(store_dir)
    payload = build_payload(event, store)
    result = ee.run_pipeline(payload)
    persist_store(store_dir, payload, result)
    return {
        "adapter": "minimal_host_adapter",
        "event_path": str(event_path),
        "store_dir": str(store_dir),
        "loaded_store": {key: bool(value) for key, value in store.items()},
        "persisted": {
            "user_profile": str(store_dir / STORE_FILES["user_profile"]),
            "last_state": str(store_dir / STORE_FILES["last_state"]),
            "calibration_state": str(store_dir / STORE_FILES["calibration_state"]),
        },
        "result": result,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Minimal host adapter for the emotion skill.")
    parser.add_argument("--event", required=True, help="Path to a host event JSON payload.")
    parser.add_argument("--store-dir", required=True, help="Directory for persisted profile, state, and calibration files.")
    parser.add_argument("--output", help="Optional path for the rendered output JSON.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    event_path = Path(args.event)
    store_dir = Path(args.store_dir)
    if not event_path.exists():
        parser.exit(2, f"Host event file not found: {event_path}\n")
    try:
        rendered_obj = run_event(event_path, store_dir, args.pretty)
    except json.JSONDecodeError as exc:
        parser.exit(2, f"Invalid JSON input: {exc}\n")
    except ValueError as exc:
        parser.exit(2, f"{exc}\n")
    rendered = dump_json(rendered_obj, args.pretty)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
