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
        "schema_version",
        "degraded",
        "degradation_reasons",
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

    host_code, host_raw = run_command(
        [sys.executable, "scripts/emotion_engine.py", "host", "--input", str(DEMO_EVENT), "--pretty"]
    )
    try:
        host_parsed = json.loads(host_raw) if host_raw else {}
    except json.JSONDecodeError:
        host_parsed = {}
    host_contract_ok = (
        host_code == 0
        and isinstance(host_parsed, dict)
        and "overlay_prompt" in host_parsed
        and "routing" in host_parsed
        and "features" not in host_parsed
        and "prompts" not in host_parsed
        and isinstance(host_parsed.get("memory"), dict)
    )
    record(
        "host_output_contract",
        host_contract_ok,
        {"exit_code": host_code, "keys": sorted(host_parsed.keys()) if isinstance(host_parsed, dict) else [], "raw": host_raw[:400]},
        findings,
    )

    degraded = ee.run_pipeline(
        {
            "message": "Show me the exact failing step.",
            "context": "bad",
            "runtime": "bad",
            "user_profile": {"baseline": "bad", "timezone": "Bad/Zone"},
            "history": "bad",
            "llm_semantic": "bad",
        }
    )
    degraded_ok = (
        isinstance(degraded, dict)
        and degraded.get("degraded") is True
        and isinstance(degraded.get("degradation_reasons"), list)
        and isinstance(degraded.get("confirmed_state"), dict)
        and isinstance(degraded["confirmed_state"].get("dominant_mode"), str)
    )
    record(
        "malformed_payload_degrades_not_crash",
        degraded_ok,
        {
            "degraded": degraded.get("degraded"),
            "degradation_reasons": degraded.get("degradation_reasons"),
            "mode": degraded.get("confirmed_state", {}).get("dominant_mode"),
        },
        findings,
    )

    recovered_mapping = ee.run_pipeline(
        {
            "message": "先给我依据，别瞎猜",
            "context": "{\"timezone\":\"Asia/Shanghai\",\"now_iso\":\"2026-04-23T10:00:00+08:00\"}",
            "user_profile": "{\"timezone\":\"Asia/Shanghai\",\"baseline\":{\"response_delay_seconds\":12},\"persona_traits\":{\"caution\":0.7}}",
        }
    )
    recovered_mapping_ok = (
        recovered_mapping.get("degraded") is True
        and "context_not_mapping.parsed_from_json_string" in recovered_mapping.get("degradation_reasons", [])
        and "user_profile_not_mapping.parsed_from_json_string" in recovered_mapping.get("degradation_reasons", [])
        and recovered_mapping["profile_state"]["local_hour"] == 10
        and recovered_mapping["profile_state"]["persona_source"] == "persona_traits"
    )
    record(
        "json_string_mapping_recovery",
        recovered_mapping_ok,
        {
            "degraded": recovered_mapping.get("degraded"),
            "degradation_reasons": recovered_mapping.get("degradation_reasons"),
            "profile_state": recovered_mapping.get("profile_state"),
        },
        findings,
    )

    label_input = ee.run_pipeline(
        {
            "message": "先给我依据，别瞎猜",
            "llm_semantic": {
                "labels": ["skeptical", None, {"bad": True}, "skeptical", ""],
                "confidence": 0.88,
                "emotion_vector": {
                    "urgency": 0.1,
                    "frustration": 0.1,
                    "confusion": 0.06,
                    "skepticism": 0.9,
                    "satisfaction": 0.04,
                    "cautiousness": 0.2,
                    "openness": 0.08,
                },
            },
        }
    )
    label_input_ok = (
        label_input.get("degraded") is True
        and "llm_semantic.labels_not_list.contains_non_string" in label_input.get("degradation_reasons", [])
        and label_input["confirmed_state"]["labels"].count("skeptical") == 1
    )
    record(
        "label_list_non_string_guard",
        label_input_ok,
        {
            "degraded": label_input.get("degraded"),
            "degradation_reasons": label_input.get("degradation_reasons"),
            "labels": label_input["confirmed_state"]["labels"],
        },
        findings,
    )

    bad_history = ee.run_pipeline(
        {
            "message": "show me the exact failing path",
            "history": [
                {"role": {"bad": True}, "text": {"oops": 1}},
                {"role": 7, "text": 12},
                {"content": ["nested", "list"]},
            ],
        }
    )
    history_guard_ok = (
        bad_history.get("degraded") is True
        and any(reason.startswith("history_item_0_") for reason in bad_history.get("degradation_reasons", []))
        and "{'oops': 1}" not in json.dumps(bad_history["features"], ensure_ascii=False)
    )
    record(
        "history_non_string_guard",
        history_guard_ok,
        {
            "degraded": bad_history.get("degraded"),
            "degradation_reasons": bad_history.get("degradation_reasons"),
            "history_count": len(bad_history.get("features", {}).get("recent_user_messages", []) or []),
        },
        findings,
    )

    degradation_flood = ee.run_pipeline(
        {
            "message": "show me the exact failing path",
            "history": [object() for _ in range(40)],
        }
    )
    flood_reasons = degradation_flood.get("degradation_reasons", [])
    degradation_cap_ok = (
        degradation_flood.get("degraded") is True
        and len(flood_reasons) <= ee.MAX_DEGRADATION_REASONS
        and any(reason.startswith("...+") for reason in flood_reasons)
    )
    record(
        "degradation_reason_cap",
        degradation_cap_ok,
        {
            "count": len(flood_reasons),
            "tail": flood_reasons[-3:],
        },
        findings,
    )

    deterministic_hour = ee.run_pipeline({"message": "ping", "user_profile": {"timezone": "Asia/Shanghai"}})
    deterministic_hour_ok = deterministic_hour["profile_state"]["local_hour"] is None and deterministic_hour.get("degraded") is False
    record(
        "deterministic_local_hour_without_now_iso",
        deterministic_hour_ok,
        {
            "local_hour": deterministic_hour["profile_state"]["local_hour"],
            "degraded": deterministic_hour.get("degraded"),
            "degradation_reasons": deterministic_hour.get("degradation_reasons"),
        },
        findings,
    )

    base_weight_features = {
        "unresolved_turns": 0,
        "user_profile": {
            "affective_prior_source": "default",
            "persona_source": "default",
        },
    }
    weight_boundary_cases = [
        (
            "bootstrap_floor",
            {"observed_turns": 0, "posthoc_samples": 0, "consistency_samples": 0, "prediction_agreement": 0.0, "consistency_rate": 1.0},
            {"stage": "bootstrap", "effective_consistency": 0.0},
        ),
        (
            "calibrating_mid",
            {"observed_turns": 12, "posthoc_samples": 8, "consistency_samples": 8, "prediction_agreement": 0.0, "consistency_rate": 0.0},
            {"stage": "calibrating"},
        ),
        (
            "stable_ceiling",
            {"observed_turns": 30, "posthoc_samples": 24, "consistency_samples": 18, "stable_prediction_hits": 18, "prediction_agreement": 1.0, "consistency_rate": 1.0},
            {"stage": "stable", "effective_consistency": 1.0},
        ),
    ]
    weight_boundary_results = []
    for name, calibration_state, expected in weight_boundary_cases:
        schedule = ee.build_weight_schedule({"calibration_state": calibration_state}, base_weight_features)
        weight_boundary_results.append({"name": name, "schedule": schedule, "expected": expected})
    weight_schedule_ok = (
        weight_boundary_results[0]["schedule"]["stage"] == "bootstrap"
        and weight_boundary_results[0]["schedule"]["effective_consistency"] == 0.0
        and weight_boundary_results[1]["schedule"]["stage"] == "calibrating"
        and weight_boundary_results[2]["schedule"]["stage"] == "stable"
        and weight_boundary_results[2]["schedule"]["effective_consistency"] == 1.0
    )
    record(
        "weight_schedule_boundaries",
        weight_schedule_ok,
        {"results": weight_boundary_results},
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
        preview_code, preview_raw = run_command(
            [
                sys.executable,
                "scripts/minimal_host_adapter.py",
                "--event",
                str(DEMO_EVENT),
                "--store-dir",
                str(Path(tmp_dir) / "preview-store"),
                "--view",
                "host",
                "--no-persist",
                "--pretty",
            ]
        )
        try:
            preview_parsed = json.loads(preview_raw) if preview_raw else {}
        except json.JSONDecodeError:
            preview_parsed = {}
        adapter_preview_ok = (
            preview_code == 0
            and isinstance(preview_parsed, dict)
            and preview_parsed.get("persist_enabled") is False
            and preview_parsed.get("persisted") == {}
            and "overlay_prompt" in (preview_parsed.get("result") or {})
        )
        record(
            "adapter_preview_no_persist",
            adapter_preview_ok,
            {
                "exit_code": preview_code,
                "persist_enabled": preview_parsed.get("persist_enabled") if isinstance(preview_parsed, dict) else None,
                "result_keys": sorted((preview_parsed.get("result") or {}).keys()) if isinstance(preview_parsed, dict) else [],
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
