#!/usr/bin/env python3
from __future__ import annotations

import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import community_long_tail_cases as long_tail
import emotion_engine as ee
import smoke_test as smoke


ROOT = Path(__file__).resolve().parents[1]
DEMO_EVENT = ROOT / "demo" / "local_history_event.json"


def record(name: str, ok: bool, detail: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    findings.append({"name": name, "ok": ok, "detail": detail})


def run_command(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(args, capture_output=True, text=True, cwd=ROOT)
    raw = proc.stdout.strip() or proc.stderr.strip()
    return proc.returncode, raw


def main() -> int:
    findings: list[dict[str, Any]] = []

    demo_payload = json.loads(DEMO_EVENT.read_text(encoding="utf-8"))
    demo_result = ee.run_pipeline(demo_payload)
    required_top_level = {
        "profile_state",
        "memory_update",
        "weight_schedule",
        "collection_stack",
        "consistency_snapshot",
        "review_plan",
        "posthoc_plan",
        "review_shadow",
        "features",
        "confirmed_state",
        "prediction",
        "analysis",
        "routing",
        "guidance",
        "overlay_prompt",
        "prompts",
    }
    schema_ok = required_top_level.issubset(set(demo_result))
    record(
        "schema_contract",
        schema_ok,
        {"missing": sorted(required_top_level - set(demo_result))},
        findings,
    )

    base = ee.run_pipeline({"message": "先给我依据，别瞎猜"})
    with_llm = ee.run_pipeline(
        {
            "message": "先给我依据，别瞎猜",
            "llm_semantic": {
                "labels": ["skeptical"],
                "confidence": 0.91,
                "emotion_vector": {
                    "urgency": 0.18,
                    "frustration": 0.12,
                    "confusion": 0.08,
                    "skepticism": 0.92,
                    "satisfaction": 0.04,
                    "cautiousness": 0.18,
                    "openness": 0.12
                }
            }
        }
    )
    llm_contract_ok = base["confirmed_state"]["vector"] != with_llm["confirmed_state"]["vector"] and "skeptical" in with_llm["confirmed_state"]["labels"]
    record(
        "llm_semantic_emotion_vector_contract",
        llm_contract_ok,
        {
            "base_vector": base["confirmed_state"]["vector"],
            "with_llm_vector": with_llm["confirmed_state"]["vector"],
            "with_llm_labels": with_llm["confirmed_state"]["labels"],
        },
        findings,
    )

    missing_code, missing_raw = run_command(
        [sys.executable, "scripts/emotion_engine.py", "run", "--input", "missing-turn.json", "--pretty"]
    )
    missing_file_ok = missing_code != 0 and "JSON input file not found" in missing_raw
    record(
        "friendly_missing_file_error",
        missing_file_ok,
        {"exit_code": missing_code, "raw": missing_raw},
        findings,
    )

    oracle_row_a = {"message": "Compare the two paths and keep protected files untouched.", "expected_labels": ["skeptical", "cautious"]}
    oracle_row_b = {"message": "Compare the two paths and keep protected files untouched.", "expected_labels": ["urgent", "frustrated"]}
    payload_a = smoke.build_community_payload(oracle_row_a, random.Random(20260421))
    payload_b = smoke.build_community_payload(oracle_row_b, random.Random(20260421))
    oracle_guard_ok = payload_a == payload_b
    record(
        "community_payload_oracle_guard",
        oracle_guard_ok,
        {"payload_a": payload_a, "payload_b": payload_b},
        findings,
    )

    community_index = smoke.index_rows(smoke.load_jsonl(smoke.COMMUNITY_DATASET))
    missing_long_tail_ids = []
    for cluster in long_tail.LONG_TAIL_CLUSTERS:
        missing_long_tail_ids.extend([row_id for row_id in cluster["smoke_ids"] if row_id not in community_index])
    record(
        "long_tail_cluster_dataset_guard",
        not missing_long_tail_ids,
        {"missing_ids": missing_long_tail_ids, "cluster_count": len(long_tail.LONG_TAIL_CLUSTERS)},
        findings,
    )

    exploratory = ee.run_pipeline({"message": "给我两个方案和取舍，先看结构差异。"})
    false_positive_ok = exploratory["confirmed_state"]["dominant_mode"] == "exploratory" and "urgent" not in exploratory["confirmed_state"]["labels"] and "frustrated" not in exploratory["confirmed_state"]["labels"]
    record(
        "false_positive_guard",
        false_positive_ok,
        {
            "mode": exploratory["confirmed_state"]["dominant_mode"],
            "labels": exploratory["confirmed_state"]["labels"],
        },
        findings,
    )

    satisfied = ee.run_pipeline({"message": "好了，主流程通了，开始收口"})
    release_guard_ok = satisfied["confirmed_state"]["dominant_mode"] == "satisfied" and satisfied["routing"]["reply_style"] == "guard_then_close"
    record(
        "post_success_guard",
        release_guard_ok,
        {
            "mode": satisfied["confirmed_state"]["dominant_mode"],
            "reply_style": satisfied["routing"]["reply_style"],
            "labels": satisfied["confirmed_state"]["labels"],
        },
        findings,
    )

    with tempfile.TemporaryDirectory(prefix="emotion-skill-audit-") as tmp_dir:
        store_dir = Path(tmp_dir) / "store"
        run_command([sys.executable, "scripts/minimal_host_adapter.py", "--event", str(DEMO_EVENT), "--store-dir", str(store_dir)])
        second_code, second_raw = run_command([sys.executable, "scripts/minimal_host_adapter.py", "--event", str(DEMO_EVENT), "--store-dir", str(store_dir), "--pretty"])
        try:
            second_parsed = json.loads(second_raw) if second_raw else {}
        except json.JSONDecodeError:
            second_parsed = {}
        adapter_ok = second_code == 0 and isinstance(second_parsed, dict) and all(second_parsed.get("loaded_store", {}).values())
        record(
            "adapter_persistence",
            adapter_ok,
            {
                "exit_code": second_code,
                "loaded_store": second_parsed.get("loaded_store"),
            },
            findings,
        )

    market_code, market_raw = run_command([sys.executable, "scripts/marketplace_tag_audit.py"])
    try:
        market_parsed = json.loads(market_raw) if market_raw else {}
    except json.JSONDecodeError:
        market_parsed = {}
    market_ok = market_code == 0 and isinstance(market_parsed, dict) and bool(market_parsed.get("ok"))
    listing = market_parsed.get("smoke", {}).get("listing_copy", {}) if isinstance(market_parsed, dict) else {}
    full_surface = market_parsed.get("smoke", {}).get("full_surface", {}) if isinstance(market_parsed, dict) else {}
    record(
        "marketplace_tag_scope",
        market_ok and listing.get("predicted_domain") == "development_orchestration" and full_surface.get("predicted_domain") == "development_orchestration" and not any((listing.get("capabilities") or {}).values()) and not any((full_surface.get("capabilities") or {}).values()),
        {
            "exit_code": market_code,
            "listing_copy": listing,
            "full_surface": full_surface,
        },
        findings,
    )

    ok = all(item["ok"] for item in findings)
    print(json.dumps({"ok": ok, "findings": findings}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
