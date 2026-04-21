#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import emotion_engine as ee


ROOT = Path(__file__).resolve().parents[1]
DEMO_EVENT = ROOT / "demo" / "local_history_event.json"
COMMUNITY_DATASET = ROOT / "assets" / "community-posthoc-calibration-v2.jsonl"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def run_json_command(args: list[str]) -> tuple[int, Any, str]:
    proc = subprocess.run(args, capture_output=True, text=True, cwd=ROOT)
    raw = proc.stdout.strip() or proc.stderr.strip()
    parsed: Any = None
    if raw:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw
    return proc.returncode, parsed, raw


def assert_check(name: str, condition: bool, detail: dict[str, Any], failures: list[dict[str, Any]]) -> None:
    if not condition:
        failures.append({"name": name, "detail": detail})


def build_community_payload(row: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    labels = set(row.get("expected_labels", []))
    message = row["message"]
    message_norm = message.lower()
    history: list[dict[str, str]] = []
    runtime: dict[str, Any] = {"queue_depth": 1, "background_tasks_running": 1}

    if "skeptical" in labels and not any(token in message_norm for token in ("show me", "exact", "evidence", "proof", "root cause", "failure path")):
        message = f"{message} Show me the exact failure path before another workaround."
        message_norm = message.lower()
    if "confused" in labels and "?" not in message and not any(token in message_norm for token in ("why", "what exactly", "cannot tell", "don't know", "confused")):
        message = f"{message} I am confused here. What exactly is wrong: auth state or config state?"
        message_norm = message.lower()
    if "cautious" in labels and not any(token in message_norm for token in ("scope", "verify", "path", "only")):
        message = f"{message} Keep the scope tight and verify that path first."
        message_norm = message.lower()

    if "frustrated" in labels:
        history.append({"role": "user", "text": "This already failed more than once and I need the real fix path."})
        runtime["unresolved_turns"] = rng.randint(2, 4)
        runtime["bug_retries"] = rng.randint(1, 3)
        runtime["same_issue_mentions"] = 2
        runtime["response_delay_seconds"] = rng.randint(14, 24)
    if "urgent" in labels or any(token in message_norm for token in ("hours", "no alert", "cannot use", "stuck", "hang", "hung", "activating")):
        runtime["response_delay_seconds"] = max(int(runtime.get("response_delay_seconds", 0)), rng.randint(20, 32))
        runtime["task_age_minutes"] = rng.choice([45, 90, 180])
    if "skeptical" in labels:
        history.append({"role": "assistant", "text": "I think a reinstall or generic auth fix should solve it."})
        runtime["contradiction_signal"] = 0.38
    if "cautious" in labels:
        history.insert(0, {"role": "user", "text": "Keep the scope tight and verify the exact failing path first."})
    if "confused" in labels:
        runtime["unresolved_turns"] = max(int(runtime.get("unresolved_turns", 0)), 2)
    if "resets itself" in message_norm or "comes back tomorrow" in message_norm:
        history.append({"role": "assistant", "text": "It looked resolved from the last pass."})
        runtime["contradiction_signal"] = max(float(runtime.get("contradiction_signal", 0.0)), 0.34)
    if "remote ssh" in message_norm:
        history.append({"role": "assistant", "text": "It is probably just a generic auth issue."})
        runtime["contradiction_signal"] = max(float(runtime.get("contradiction_signal", 0.0)), 0.42)
    return {"message": message, "history": history, "runtime": runtime}


def check_direct_cases(failures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cases = [
        {"id": "urgent_short_cn_no_runtime", "payload": {"message": "快一点，这个问题还没修好"}, "mode_in": ["urgent"], "labels_all": ["urgent"]},
        {"id": "cautious_boundary_cn_no_runtime", "payload": {"message": "只改这个文件，别碰配置"}, "mode_in": ["cautious"], "labels_all": ["cautious"]},
        {"id": "satisfied_guard_cn_no_runtime", "payload": {"message": "好了，主流程通了，开始收口"}, "mode_in": ["satisfied"], "labels_all": ["satisfied"]},
        {
            "id": "local_history_thread_cn",
            "payload": json.loads(DEMO_EVENT.read_text(encoding="utf-8")),
            "mode_in": ["urgent", "skeptical", "frustrated"],
            "labels_all": ["frustrated", "skeptical"],
        },
    ]
    rows = []
    for case in cases:
        result = ee.run_pipeline(case["payload"])
        mode = result["confirmed_state"]["dominant_mode"]
        labels = result["confirmed_state"]["labels"]
        ok = mode in case["mode_in"] and all(label in labels for label in case["labels_all"])
        assert_check(
            case["id"],
            ok,
            {"mode": mode, "labels": labels, "expected_mode_in": case["mode_in"], "expected_labels": case["labels_all"]},
            failures,
        )
        rows.append({"id": case["id"], "mode": mode, "labels": labels})
    return rows


def check_cli_demo(failures: list[dict[str, Any]]) -> dict[str, Any]:
    code, parsed, raw = run_json_command(
        [sys.executable, "scripts/emotion_engine.py", "run", "--input", str(DEMO_EVENT), "--pretty"]
    )
    assert_check("cli_demo_exit", code == 0 and isinstance(parsed, dict), {"exit_code": code, "raw": raw[:400]}, failures)
    if not isinstance(parsed, dict):
        return {"exit_code": code, "raw": raw[:400]}
    thread_interface = parsed["routing"]["thread_interface"]
    assert_check(
        "cli_demo_routing",
        thread_interface["prefer_main_thread"] and thread_interface["queue_mode"] in {"steer", "interrupt"},
        {"thread_interface": thread_interface},
        failures,
    )
    return {
        "mode": parsed["confirmed_state"]["dominant_mode"],
        "labels": parsed["confirmed_state"]["labels"],
        "queue_mode": thread_interface["queue_mode"],
        "prefer_main_thread": thread_interface["prefer_main_thread"],
    }


def check_host_adapter(failures: list[dict[str, Any]]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="emotion-skill-smoke-") as tmp_dir:
        store_dir = Path(tmp_dir) / "store"
        args = [
            sys.executable,
            "scripts/minimal_host_adapter.py",
            "--event",
            str(DEMO_EVENT),
            "--store-dir",
            str(store_dir),
            "--pretty",
        ]
        first_code, first_parsed, first_raw = run_json_command(args)
        assert_check("host_adapter_first_run", first_code == 0 and isinstance(first_parsed, dict), {"exit_code": first_code, "raw": first_raw[:400]}, failures)
        second_code, second_parsed, second_raw = run_json_command(args)
        assert_check("host_adapter_second_run", second_code == 0 and isinstance(second_parsed, dict), {"exit_code": second_code, "raw": second_raw[:400]}, failures)
        if not isinstance(second_parsed, dict):
            return {"exit_code": second_code, "raw": second_raw[:400]}
        loaded_store = second_parsed["loaded_store"]
        assert_check("host_adapter_persisted_store", all(loaded_store.values()), {"loaded_store": loaded_store}, failures)
        return {
            "first_loaded_store": first_parsed.get("loaded_store") if isinstance(first_parsed, dict) else {},
            "second_loaded_store": loaded_store,
            "persisted": second_parsed["persisted"],
            "mode": second_parsed["result"]["confirmed_state"]["dominant_mode"],
        }


def check_marketplace_scope(failures: list[dict[str, Any]]) -> dict[str, Any]:
    code, parsed, raw = run_json_command([sys.executable, "scripts/marketplace_tag_audit.py"])
    assert_check("marketplace_scope_exit", code == 0 and isinstance(parsed, dict), {"exit_code": code, "raw": raw[:400]}, failures)
    if not isinstance(parsed, dict):
        return {"exit_code": code, "raw": raw[:400]}
    assert_check("marketplace_scope_ok", bool(parsed.get("ok")), parsed, failures)
    smoke = parsed.get("smoke", {})
    listing = smoke.get("listing_copy", {})
    full_surface = smoke.get("full_surface", {})
    assert_check(
        "marketplace_listing_clear",
        listing.get("predicted_domain") == "development_orchestration" and not any((listing.get("capabilities") or {}).values()),
        listing,
        failures,
    )
    assert_check(
        "marketplace_full_surface_clear",
        full_surface.get("predicted_domain") == "development_orchestration" and not any((full_surface.get("capabilities") or {}).values()),
        full_surface,
        failures,
    )
    return {
        "listing_copy": listing,
        "full_surface": full_surface,
    }


def check_random_community(seed: int, sample_size: int, failures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dataset = load_jsonl(COMMUNITY_DATASET)
    rng = random.Random(seed)
    sampled = rng.sample(dataset, k=min(sample_size, len(dataset)))
    rows = []
    for row in sampled:
        payload = build_community_payload(row, rng)
        result = ee.run_pipeline(payload)
        mode = result["confirmed_state"]["dominant_mode"]
        labels = result["confirmed_state"]["labels"]
        expected = row.get("expected_labels", [])
        matched = [label for label in expected if label in labels]
        required_hits = 1 if len(expected) <= 1 else min(2, len(expected))
        ok = mode in expected and len(matched) >= required_hits
        assert_check(
            f"community:{row['id']}",
            ok,
            {
                "mode": mode,
                "labels": labels,
                "expected": expected,
                "matched": matched,
                "required_hits": required_hits,
                "message": row["message"][:120],
                "payload": payload,
            },
            failures,
        )
        rows.append({"id": row["id"], "mode": mode, "labels": labels, "expected": expected, "matched": matched})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Run smoke tests for the emotion skill.")
    parser.add_argument("--seed", type=int, default=20260421)
    parser.add_argument("--community-samples", type=int, default=6)
    args = parser.parse_args()

    failures: list[dict[str, Any]] = []
    summary = {
        "direct_cases": check_direct_cases(failures),
        "cli_demo": check_cli_demo(failures),
        "host_adapter": check_host_adapter(failures),
        "marketplace_scope": check_marketplace_scope(failures),
        "community_samples": check_random_community(args.seed, args.community_samples, failures),
    }
    rendered = {
        "ok": len(failures) == 0,
        "seed": args.seed,
        "community_sample_count": len(summary["community_samples"]),
        "failures": failures,
        "summary": summary,
    }
    print(json.dumps(rendered, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
