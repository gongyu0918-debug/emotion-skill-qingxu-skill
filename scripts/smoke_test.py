#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import community_long_tail_cases as long_tail
import emotion_engine as ee


ROOT = Path(__file__).resolve().parents[1]
DEMO_EVENT = ROOT / "demo" / "local_history_event.json"
COMMUNITY_DATASET = ROOT / "assets" / "community-posthoc-calibration-v2.jsonl"
STALL_HINTS = re.compile(r"(hang|hung|stuck|freeze|freezes|freezing|no response|nothing changes|still not fixed|again|fails|timeout|redirected back|卡住|卡死|没反应|一直转)", re.IGNORECASE)
PRESSURE_HINTS = re.compile(r"(for hours|hour|hours|release|regression|blocked|blocking|ship today|发布|上线|回归)", re.IGNORECASE)
SKEPTICAL_HINTS = re.compile(r"(show me|evidence|proof|exact|root cause|before another workaround|别瞎猜|依据|证据|根因|what changed|which setting|trust)", re.IGNORECASE)
CAUTIOUS_HINTS = re.compile(r"(scope|verify|safe|conservative|stable path|guardrails|protected files|before any more edits|repo-wide changes|别碰|只改|验证|保守|稳定路径|保护文件)", re.IGNORECASE)
COMPARISON_HINTS = re.compile(r"(compare|two ways|two paths|two options|tradeoff|tradeoffs|what changed|difference|differences|对比|比较|取舍|两个方案|两条路径)", re.IGNORECASE)
CONFUSION_HINTS = re.compile(r"(confused|unclear|cannot tell|can't tell|what exactly is wrong|which state|which one|不清楚|看不懂|分不清|哪一步)", re.IGNORECASE)
TOOL_RESULT_HINTS = re.compile(r"(tool[_ ]result|tool[_ ]use|non-existent tool|missing tool result|dead state)", re.IGNORECASE)
SHARED_CONTEXT_HINTS = re.compile(r"(shared context|prompt guessing|conversational thread|starts fresh|fresh session|forgets this rule|context plumbing|compaction|session reset)", re.IGNORECASE)
PATH_HINTS = re.compile(r"(file path|special character|path handling|path resolution|quoting|escaping)", re.IGNORECASE)
REPO_HINTS = re.compile(r"(repo|codebase|guesswork|guessed the rest|grounded in the repo|grounded in the codebase|blind assumption)", re.IGNORECASE)
ALERT_HINTS = re.compile(r"(no alert|no notification|nobody noticed|silently broke|showed up late|manual refresh|nothing happened|goes quiet|scheduled time)", re.IGNORECASE)
SIGNIN_HINTS = re.compile(r"(sign-in loop|activation loop|activating for hours|cannot use the extension)", re.IGNORECASE)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def index_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in rows}


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
    message = row["message"]
    message_norm = message.lower()
    history: list[dict[str, str]] = []
    runtime: dict[str, Any] = {"queue_depth": 1, "background_tasks_running": 1}

    if STALL_HINTS.search(message):
        history.append({"role": "user", "text": "This already failed more than once and I need the real fix path."})
        runtime["unresolved_turns"] = rng.randint(1, 4)
        runtime["same_issue_mentions"] = rng.randint(1, 2)
        runtime["response_delay_seconds"] = rng.randint(14, 28)
    if PRESSURE_HINTS.search(message):
        runtime["response_delay_seconds"] = max(int(runtime.get("response_delay_seconds", 0)), rng.randint(18, 32))
        runtime["task_age_minutes"] = rng.choice([45, 90, 180])
        runtime["bug_retries"] = max(int(runtime.get("bug_retries", 0)), rng.randint(1, 3))
    if SKEPTICAL_HINTS.search(message):
        history.append({"role": "assistant", "text": "I think a reinstall or generic auth fix should solve it."})
        runtime["contradiction_signal"] = max(float(runtime.get("contradiction_signal", 0.0)), 0.38)
    if CAUTIOUS_HINTS.search(message):
        history.insert(0, {"role": "user", "text": "Keep the scope tight and verify the exact failing path first."})
    if COMPARISON_HINTS.search(message):
        history.append({"role": "assistant", "text": "It looked resolved from the last pass, but we did not compare the alternative path."})
        runtime["contradiction_signal"] = max(float(runtime.get("contradiction_signal", 0.0)), 0.3)
    if CONFUSION_HINTS.search(message):
        runtime["unresolved_turns"] = max(int(runtime.get("unresolved_turns", 0)), 2)
    if "resets itself" in message_norm or "comes back tomorrow" in message_norm:
        history.append({"role": "assistant", "text": "It looked resolved from the last pass."})
        runtime["contradiction_signal"] = max(float(runtime.get("contradiction_signal", 0.0)), 0.34)
    if "worked yesterday" in message_norm or "broke it today" in message_norm:
        history.append({"role": "assistant", "text": "The last release looked healthy in a prior run."})
        runtime["contradiction_signal"] = max(float(runtime.get("contradiction_signal", 0.0)), 0.36)
    if "remote ssh" in message_norm:
        history.append({"role": "assistant", "text": "It is probably just a generic auth issue."})
        runtime["contradiction_signal"] = max(float(runtime.get("contradiction_signal", 0.0)), 0.42)
    if TOOL_RESULT_HINTS.search(message):
        history.append({"role": "assistant", "text": "The tool path probably resolved and the dead state should clear on retry."})
        history.insert(0, {"role": "user", "text": "Recover safely and show the missing tool result before the next retry."})
        runtime["unresolved_turns"] = max(int(runtime.get("unresolved_turns", 0)), 2)
        runtime["same_issue_mentions"] = max(int(runtime.get("same_issue_mentions", 0)), 2)
        runtime["contradiction_signal"] = max(float(runtime.get("contradiction_signal", 0.0)), 0.34)
    if SHARED_CONTEXT_HINTS.search(message):
        history.append({"role": "assistant", "text": "I can infer the missing context from the latest prompt."})
        history.insert(0, {"role": "user", "text": "Verify the shared context and keep the handoff path scoped."})
        runtime["unresolved_turns"] = max(int(runtime.get("unresolved_turns", 0)), 2)
        runtime["same_issue_mentions"] = max(int(runtime.get("same_issue_mentions", 0)), 2)
        runtime["contradiction_signal"] = max(float(runtime.get("contradiction_signal", 0.0)), 0.3)
    if PATH_HINTS.search(message):
        history.append({"role": "assistant", "text": "It is probably just shell escaping."})
        runtime["unresolved_turns"] = max(int(runtime.get("unresolved_turns", 0)), 1)
        runtime["contradiction_signal"] = max(float(runtime.get("contradiction_signal", 0.0)), 0.24)
    if REPO_HINTS.search(message):
        history.append({"role": "assistant", "text": "I only checked one folder, but the rest should behave the same."})
        runtime["unresolved_turns"] = max(int(runtime.get("unresolved_turns", 0)), 1)
        runtime["contradiction_signal"] = max(float(runtime.get("contradiction_signal", 0.0)), 0.32)
    if ALERT_HINTS.search(message):
        history.append({"role": "assistant", "text": "The scheduler looked healthy in the last pass."})
        runtime["response_delay_seconds"] = max(int(runtime.get("response_delay_seconds", 0)), rng.randint(16, 28))
        runtime["task_age_minutes"] = max(int(runtime.get("task_age_minutes", 0)), rng.choice([120, 180, 240]))
        runtime["bug_retries"] = max(int(runtime.get("bug_retries", 0)), rng.randint(1, 2))
        runtime["contradiction_signal"] = max(float(runtime.get("contradiction_signal", 0.0)), 0.28)
    if SIGNIN_HINTS.search(message):
        history.append({"role": "assistant", "text": "The extension looks authenticated, so the loop should clear after a refresh."})
        runtime["unresolved_turns"] = max(int(runtime.get("unresolved_turns", 0)), 2)
        runtime["bug_retries"] = max(int(runtime.get("bug_retries", 0)), 1)
        runtime["same_issue_mentions"] = max(int(runtime.get("same_issue_mentions", 0)), 2)
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


def check_long_tail_clusters(seed: int, failures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dataset = index_rows(load_jsonl(COMMUNITY_DATASET))
    rows: list[dict[str, Any]] = []
    for index, cluster in enumerate(long_tail.LONG_TAIL_CLUSTERS):
        cluster_rng = random.Random(seed + index * 97)
        cluster_results = []
        missing_ids = [row_id for row_id in cluster["smoke_ids"] if row_id not in dataset]
        assert_check(
            f"long_tail_cluster:{cluster['id']}:dataset_ids",
            not missing_ids,
            {"cluster_id": cluster["id"], "missing_ids": missing_ids},
            failures,
        )
        for row_id in cluster["smoke_ids"]:
            row = dataset.get(row_id)
            if not row:
                continue
            payload = build_community_payload(row, cluster_rng)
            result = ee.run_pipeline(payload)
            mode = result["confirmed_state"]["dominant_mode"]
            labels = result["confirmed_state"]["labels"]
            smoke_expect = cluster.get("smoke_expect") or {}
            expected = smoke_expect.get("labels_all") or row.get("expected_labels", [])
            mode_in = smoke_expect.get("mode_in") or expected
            matched = [label for label in expected if label in labels]
            required_hits = 1 if len(expected) <= 1 else min(2, len(expected))
            ok = mode in mode_in and len(matched) >= required_hits
            assert_check(
                f"long_tail_cluster:{cluster['id']}:{row_id}",
                ok,
                {
                    "cluster_id": cluster["id"],
                    "theme": cluster["theme"],
                    "mode": mode,
                    "labels": labels,
                    "mode_in": mode_in,
                    "expected": expected,
                    "matched": matched,
                    "required_hits": required_hits,
                    "message": row["message"],
                    "payload": payload,
                },
                failures,
            )
            cluster_results.append({"id": row_id, "mode": mode, "labels": labels, "mode_in": mode_in, "expected": expected, "matched": matched})
        rows.append({"cluster_id": cluster["id"], "theme": cluster["theme"], "rows": cluster_results})
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
        "long_tail_clusters": check_long_tail_clusters(args.seed, failures),
        "community_samples": check_random_community(args.seed, args.community_samples, failures),
    }
    rendered = {
        "ok": len(failures) == 0,
        "seed": args.seed,
        "long_tail_cluster_count": len(summary["long_tail_clusters"]),
        "community_sample_count": len(summary["community_samples"]),
        "failures": failures,
        "summary": summary,
    }
    print(json.dumps(rendered, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
