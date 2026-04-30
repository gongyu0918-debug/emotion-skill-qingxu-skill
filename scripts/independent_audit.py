#!/usr/bin/env python3
from __future__ import annotations

import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import bundle_manifest_check
import community_long_tail_cases as long_tail
import emotion_engine as ee
import smoke_test as smoke


ROOT = Path(__file__).resolve().parents[1]
DEMO_EVENT = ROOT / "demo" / "local_history_event.json"
NEGATIVE_VALENCE_TERM_FILES = (
    ROOT / "assets" / "negative_valence_terms.en.txt",
    ROOT / "assets" / "negative_valence_terms.zh.txt",
)


def record(name: str, ok: bool, detail: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    findings.append({"name": name, "ok": ok, "detail": detail})


def run_command(args: list[str], stdin: str | None = None) -> tuple[int, str]:
    proc = subprocess.run(args, input=stdin, capture_output=True, text=True, cwd=ROOT)
    raw = proc.stdout.strip() or proc.stderr.strip()
    return proc.returncode, raw


def load_negative_valence_terms() -> list[str]:
    terms: list[str] = []
    for path in NEGATIVE_VALENCE_TERM_FILES:
        for line in path.read_text(encoding="utf-8").splitlines():
            term = line.strip().lower()
            if term and not term.startswith("#"):
                terms.append(term)
    return sorted(set(terms))


def negative_valence_hits(text: str, terms: list[str]) -> list[str]:
    haystack = text.lower()
    return [term for term in terms if term in haystack]


def prompt_addendum_samples() -> dict[str, str]:
    samples: dict[str, str] = {}
    for language in ("en", "zh"):
        for mode in ("urgent", "frustrated", "skeptical", "confused", "cautious", "satisfied", "exploratory"):
            samples[f"{language}:{mode}"] = ee.build_system_prompt_addendum(
                {"language": language},
                {"dominant_mode": mode},
                {"guard_needed": mode == "satisfied"},
            )
    return samples


def main() -> int:
    findings: list[dict[str, Any]] = []

    demo_payload = json.loads(DEMO_EVENT.read_text(encoding="utf-8"))
    demo_result = ee.run_pipeline(demo_payload)
    required_top_level = {
        "schema_version",
        "degraded",
        "degradation_reasons",
        "host_capabilities",
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
        "route_reasons",
        "response_constraints",
        "state_delta",
        "satisfaction_lock",
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

    stdin_list_code, stdin_list_raw = run_command(
        [sys.executable, "scripts/emotion_engine.py", "host", "--pretty"],
        stdin="[1,2]",
    )
    record(
        "friendly_stdin_top_level_type_error",
        stdin_list_code == 2 and "Top-level JSON object required" in stdin_list_raw and "Traceback" not in stdin_list_raw,
        {"exit_code": stdin_list_code, "raw": stdin_list_raw},
        findings,
    )

    with tempfile.TemporaryDirectory(prefix="emotion-skill-input-") as tmp_dir:
        bad_input = Path(tmp_dir) / "bad-input.json"
        bad_input.write_text("[1,2]", encoding="utf-8")
        input_list_code, input_list_raw = run_command(
            [sys.executable, "scripts/emotion_engine.py", "host", "--input", str(bad_input), "--pretty"]
        )
        record(
            "friendly_input_top_level_type_error",
            input_list_code == 2 and "Top-level JSON object required" in input_list_raw and "Traceback" not in input_list_raw,
            {"exit_code": input_list_code, "raw": input_list_raw},
            findings,
        )

        nested_output = Path(tmp_dir) / "nested" / "engine" / "emotion.json"
        nested_code, nested_raw = run_command(
            [sys.executable, "scripts/emotion_engine.py", "host", "--message", "test", "--output", str(nested_output)]
        )
        try:
            nested_parsed = json.loads(nested_output.read_text(encoding="utf-8")) if nested_output.exists() else {}
        except json.JSONDecodeError:
            nested_parsed = {}
        record(
            "engine_nested_output_write",
            nested_code == 0 and isinstance(nested_parsed, dict) and "mode" in nested_parsed,
            {"exit_code": nested_code, "raw": nested_raw, "exists": nested_output.exists()},
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
        and "labels" not in host_parsed
        and isinstance(host_parsed.get("interaction_state"), dict)
        and isinstance(host_parsed.get("route_reasons"), list)
        and all(reason in ee.ROUTE_REASON_ENUM for reason in host_parsed.get("route_reasons", []))
        and isinstance(host_parsed.get("response_constraints"), list)
        and isinstance(host_parsed.get("satisfaction_lock"), dict)
        and isinstance((host_parsed.get("guidance") or {}).get("system_prompt_addendum"), str)
        and "emotion_vector" not in (host_parsed.get("state") or {})
        and isinstance((host_parsed.get("state") or {}).get("state_delta"), dict)
        and ((host_parsed.get("state") or {}).get("_deprecated_alias") or {}).get("interaction_state") == "top_level.interaction_state"
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

    raw_host_code, raw_host_raw = run_command(
        [sys.executable, "scripts/emotion_engine.py", "host", "--input", str(DEMO_EVENT), "--include-raw-emotion", "--pretty"]
    )
    try:
        raw_host_parsed = json.loads(raw_host_raw) if raw_host_raw else {}
    except json.JSONDecodeError:
        raw_host_parsed = {}
    raw_internal = ((raw_host_parsed.get("diagnostics") or {}).get("internal") or {}) if isinstance(raw_host_parsed, dict) else {}
    raw_state_delta = raw_internal.get("state_delta") or {}
    record(
        "host_raw_emotion_opt_in",
        raw_host_code == 0
        and isinstance(raw_internal.get("labels"), list)
        and isinstance(raw_internal.get("emotion_vector"), dict)
        and isinstance(raw_state_delta, dict)
        and not str(raw_state_delta.get("dominant_shift", "")).startswith(("rising_", "falling_"))
        and "labels" not in raw_host_parsed
        and "emotion_vector" not in (raw_host_parsed.get("state") or {}),
        {
            "exit_code": raw_host_code,
            "diagnostics_keys": sorted(raw_internal.keys()) if isinstance(raw_internal, dict) else [],
            "diagnostic_dominant_shift": raw_state_delta.get("dominant_shift") if isinstance(raw_state_delta, dict) else None,
            "raw": raw_host_raw[:400],
        },
        findings,
    )

    raw_false_code, raw_false_raw = run_command(
        [sys.executable, "scripts/emotion_engine.py", "host", "--include-raw-emotion", "--pretty"],
        stdin=json.dumps(
            {
                "message": "Show me the exact failing path first.",
                "host_capabilities": {"include_raw_emotion": False},
            }
        ),
    )
    try:
        raw_false_parsed = json.loads(raw_false_raw) if raw_false_raw else {}
    except json.JSONDecodeError:
        raw_false_parsed = {}
    record(
        "host_raw_emotion_payload_false_wins",
        raw_false_code == 0 and isinstance(raw_false_parsed, dict) and "diagnostics" not in raw_false_parsed,
        {"exit_code": raw_false_code, "keys": sorted(raw_false_parsed.keys()) if isinstance(raw_false_parsed, dict) else [], "raw": raw_false_raw[:400]},
        findings,
    )

    raw_string_false_code, raw_string_false_raw = run_command(
        [sys.executable, "scripts/emotion_engine.py", "host", "--include-raw-emotion", "--pretty"],
        stdin=json.dumps(
            {
                "message": "Show me the exact failing path first.",
                "host_capabilities": {"include_raw_emotion": "false"},
            }
        ),
    )
    try:
        raw_string_false_parsed = json.loads(raw_string_false_raw) if raw_string_false_raw else {}
    except json.JSONDecodeError:
        raw_string_false_parsed = {}
    record(
        "host_raw_emotion_string_false_wins",
        raw_string_false_code == 0 and isinstance(raw_string_false_parsed, dict) and "diagnostics" not in raw_string_false_parsed,
        {
            "exit_code": raw_string_false_code,
            "keys": sorted(raw_string_false_parsed.keys()) if isinstance(raw_string_false_parsed, dict) else [],
            "raw": raw_string_false_raw[:400],
        },
        findings,
    )

    prompt_terms = load_negative_valence_terms()
    prompt_samples = prompt_addendum_samples()
    prompt_hits = {name: negative_valence_hits(text, prompt_terms) for name, text in prompt_samples.items()}
    record(
        "positive_prompt_addendum_no_raw_negative_terms",
        bool(prompt_samples) and all(text.strip() for text in prompt_samples.values()) and not any(prompt_hits.values()),
        {"checked": sorted(prompt_samples), "hits": {name: hits for name, hits in prompt_hits.items() if hits}},
        findings,
    )

    delta_result = ee.run_pipeline(
        {
            "message": "这个又坏了，先给我失败路径。",
            "last_state": {
                "vector": {"urgency": 0.15, "frustration": 0.12, "clarity": 0.82, "satisfaction": 0.52, "trust": 0.76, "engagement": 0.42},
                "emotion_vector": {"urgency": 0.1, "frustration": 0.12, "confusion": 0.08, "skepticism": 0.12, "satisfaction": 0.52, "cautiousness": 0.18, "openness": 0.18},
            },
            "runtime": {"bug_retries": 2, "same_issue_mentions": 2, "unresolved_turns": 2},
        }
    )
    delta_ok = (
        delta_result["state_delta"]["available"] is True
        and delta_result["state_delta"]["dominant_shift"] in {"needs_concrete_unblock", "needs_evidence_first", "needs_alignment_check", "needs_recheck", "changed"}
        and "repeat_failure_pressure" in delta_result["route_reasons"]
        and all(reason in ee.ROUTE_REASON_ENUM for reason in delta_result["route_reasons"])
        and all(need in ee.INTERACTION_NEED_ENUM for need in ee.build_host_state_delta(delta_result["state_delta"])["interaction"]["needs"])
        and isinstance(delta_result["response_constraints"], list)
    )
    record(
        "host_state_delta_and_route_reasons",
        delta_ok,
        {
            "state_delta": delta_result["state_delta"],
            "host_state_delta": ee.build_host_state_delta(delta_result["state_delta"]),
            "route_reasons": delta_result["route_reasons"],
            "response_constraints": delta_result["response_constraints"],
        },
        findings,
    )

    unsupported_language = ee.run_pipeline(
        {
            "message": "Show the verification point first.",
            "context": {"language": "ja"},
        }
    )
    record(
        "unsupported_language_fallback_marked",
        unsupported_language["features"]["language"] == "en"
        and unsupported_language["degraded"] is True
        and "unsupported_language:ja" in unsupported_language["degradation_reasons"],
        {
            "language": unsupported_language["features"]["language"],
            "degraded": unsupported_language["degraded"],
            "degradation_reasons": unsupported_language["degradation_reasons"],
        },
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
        and len(flood_reasons) == len(set(flood_reasons))
        and "degradation_reasons_truncated" in flood_reasons
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
    release_guard_ok = (
        satisfied["confirmed_state"]["dominant_mode"] == "satisfied"
        and satisfied["routing"]["reply_style"] == "guard_then_close"
        and satisfied["satisfaction_lock"]["active"] is True
        and "avoid_scope_expansion" in satisfied["response_constraints"]
    )
    record(
        "post_success_guard",
        release_guard_ok,
        {
            "mode": satisfied["confirmed_state"]["dominant_mode"],
            "reply_style": satisfied["routing"]["reply_style"],
            "labels": satisfied["confirmed_state"]["labels"],
            "satisfaction_lock": satisfied["satisfaction_lock"],
            "response_constraints": satisfied["response_constraints"],
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

        bad_event = Path(tmp_dir) / "bad-event.json"
        bad_event.write_text("[1,2]", encoding="utf-8")
        bad_event_code, bad_event_raw = run_command(
            [
                sys.executable,
                "scripts/minimal_host_adapter.py",
                "--event",
                str(bad_event),
                "--store-dir",
                str(Path(tmp_dir) / "bad-event-store"),
                "--view",
                "host",
                "--no-persist",
                "--pretty",
            ]
        )
        record(
            "adapter_top_level_type_error",
            bad_event_code == 2 and "Top-level JSON object required" in bad_event_raw and "Traceback" not in bad_event_raw,
            {"exit_code": bad_event_code, "raw": bad_event_raw},
            findings,
        )

        non_mapping_event = Path(tmp_dir) / "non-mapping-profile-event.json"
        non_mapping_event.write_text(json.dumps({"message": "先给我依据", "user_profile": "bad"}, ensure_ascii=False), encoding="utf-8")
        non_mapping_code, non_mapping_raw = run_command(
            [
                sys.executable,
                "scripts/minimal_host_adapter.py",
                "--event",
                str(non_mapping_event),
                "--store-dir",
                str(Path(tmp_dir) / "profile-store"),
                "--view",
                "host",
                "--no-persist",
                "--pretty",
            ]
        )
        try:
            non_mapping_parsed = json.loads(non_mapping_raw) if non_mapping_raw else {}
        except json.JSONDecodeError:
            non_mapping_parsed = {}
        record(
            "adapter_non_mapping_user_profile_forwarded",
            non_mapping_code == 0
            and isinstance(non_mapping_parsed, dict)
            and "user_profile_not_mapping.forwarded_to_engine" in non_mapping_parsed.get("adapter_warnings", [])
            and (non_mapping_parsed.get("result") or {}).get("degraded") is True,
            {
                "exit_code": non_mapping_code,
                "adapter_warnings": non_mapping_parsed.get("adapter_warnings") if isinstance(non_mapping_parsed, dict) else None,
                "degradation_reasons": (non_mapping_parsed.get("result") or {}).get("degradation_reasons") if isinstance(non_mapping_parsed, dict) else None,
                "raw": non_mapping_raw[:400],
            },
            findings,
        )

        corrupt_store = Path(tmp_dir) / "corrupt-store"
        corrupt_store.mkdir(parents=True, exist_ok=True)
        (corrupt_store / "user_profile.json").write_text("{bad json", encoding="utf-8")
        corrupt_code, corrupt_raw = run_command(
            [
                sys.executable,
                "scripts/minimal_host_adapter.py",
                "--event",
                str(DEMO_EVENT),
                "--store-dir",
                str(corrupt_store),
                "--view",
                "host",
                "--no-persist",
                "--pretty",
            ]
        )
        record(
            "adapter_corrupt_store_names_file",
            corrupt_code == 2 and "Invalid JSON in" in corrupt_raw and "user_profile.json" in corrupt_raw,
            {"exit_code": corrupt_code, "raw": corrupt_raw},
            findings,
        )

        ignore_code, ignore_raw = run_command(
            [
                sys.executable,
                "scripts/minimal_host_adapter.py",
                "--event",
                str(DEMO_EVENT),
                "--store-dir",
                str(corrupt_store),
                "--view",
                "host",
                "--no-persist",
                "--ignore-bad-store",
                "--pretty",
            ]
        )
        try:
            ignore_parsed = json.loads(ignore_raw) if ignore_raw else {}
        except json.JSONDecodeError:
            ignore_parsed = {}
        record(
            "adapter_ignore_bad_store",
            ignore_code == 0 and isinstance(ignore_parsed, dict) and "user_profile" in ignore_parsed.get("store_errors", {}),
            {
                "exit_code": ignore_code,
                "store_errors": ignore_parsed.get("store_errors") if isinstance(ignore_parsed, dict) else None,
                "raw": ignore_raw[:400],
            },
            findings,
        )

        adapter_output = Path(tmp_dir) / "nested" / "adapter" / "out.json"
        adapter_output_code, adapter_output_raw = run_command(
            [
                sys.executable,
                "scripts/minimal_host_adapter.py",
                "--event",
                str(DEMO_EVENT),
                "--store-dir",
                str(Path(tmp_dir) / "adapter-output-store"),
                "--view",
                "host",
                "--no-persist",
                "--output",
                str(adapter_output),
            ]
        )
        try:
            adapter_output_parsed = json.loads(adapter_output.read_text(encoding="utf-8")) if adapter_output.exists() else {}
        except json.JSONDecodeError:
            adapter_output_parsed = {}
        record(
            "adapter_nested_output_write",
            adapter_output_code == 0 and isinstance(adapter_output_parsed, dict) and "result" in adapter_output_parsed,
            {"exit_code": adapter_output_code, "raw": adapter_output_raw, "exists": adapter_output.exists()},
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

    manifest_result = bundle_manifest_check.check_manifest()
    record(
        "bundle_manifest_matches_skill_docs",
        bool(manifest_result.get("ok")),
        {
            "missing_from_docs": manifest_result.get("missing_from_docs"),
            "missing_from_bundle": manifest_result.get("missing_from_bundle"),
            "actual_count": manifest_result.get("actual_count"),
            "documented_count": manifest_result.get("documented_count"),
        },
        findings,
    )

    ok = all(item["ok"] for item in findings)
    print(json.dumps({"ok": ok, "findings": findings}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
