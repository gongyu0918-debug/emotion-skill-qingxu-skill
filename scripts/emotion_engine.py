#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import sys
import time
from typing import Any

from emotion_features import *
from emotion_output import *
from emotion_routing import *
from emotion_scoring import *
from emotion_terms import *
from emotion_types import *
from emotion_utils import *


LOGGER = logging.getLogger("emotion_skill")


def configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.WARNING)
    logging.basicConfig(level=level, stream=sys.stderr, format="%(levelname)s emotion_skill: %(message)s")


def record_profile(profile: dict[str, Any] | None, stage: str, start: float) -> None:
    if profile is not None:
        profile[stage] = round((time.perf_counter() - start) * 1000.0, 3)


def run_pipeline(payload: dict[str, Any], profile: bool = False) -> PipelineResult:
    total_start = time.perf_counter()
    pipeline_profile: dict[str, Any] | None = {} if profile else None

    stage_start = time.perf_counter()
    normalized_payload, diagnostics = normalize_payload(payload)
    record_profile(pipeline_profile, "normalize_ms", stage_start)

    stage_start = time.perf_counter()
    features = build_features(normalized_payload, diagnostics)
    profile_state = build_profile_state(features)
    constraint_signals = build_constraint_signals(features)
    weight_schedule = build_weight_schedule(normalized_payload, features, diagnostics)
    record_profile(pipeline_profile, "features_ms", stage_start)

    stage_start = time.perf_counter()
    screen = initial_screen(features)
    record_profile(pipeline_profile, "screen_ms", stage_start)

    stage_start = time.perf_counter()
    confirmed = confirm_state(normalized_payload, features, screen, weight_schedule, diagnostics)
    consistency_snapshot = build_consistency_snapshot(normalized_payload, screen, diagnostics)
    memory_update = build_memory_update(normalized_payload, features, confirmed, weight_schedule, consistency_snapshot)
    record_profile(pipeline_profile, "confirm_ms", stage_start)

    stage_start = time.perf_counter()
    prediction = predict_state(features, confirmed)
    analysis = build_analysis_plan(features, screen, confirmed, prediction)
    routing = build_routing(features, confirmed, prediction)
    state_delta = build_state_delta(normalized_payload, confirmed)
    route_reasons = build_route_reasons(features, confirmed, prediction, routing, state_delta, diagnostics)
    satisfaction_lock = build_satisfaction_lock(features, confirmed, prediction)
    response_constraints = build_response_constraints(confirmed, routing, prediction, satisfaction_lock)
    record_profile(pipeline_profile, "route_ms", stage_start)

    stage_start = time.perf_counter()
    guidance = build_guidance(features, confirmed, prediction)
    posthoc_plan = build_posthoc_plan(features, confirmed, analysis, weight_schedule)
    posthoc_shadow = build_posthoc_shadow(normalized_payload, features, confirmed, analysis, posthoc_plan, diagnostics)
    collection_stack = build_collection_stack(weight_schedule, features, posthoc_plan)
    overlay_prompt = render_overlay(features, confirmed, prediction, routing, analysis)
    debug_overlay_prompt = render_debug_overlay(features, confirmed, prediction, routing, analysis)
    record_profile(pipeline_profile, "guidance_ms", stage_start)

    stage_start = time.perf_counter()
    prompts = build_model_prompts(normalized_payload, features, screen, confirmed, routing, prediction, analysis, weight_schedule, posthoc_plan)
    prompts["overlay_prompt"] = overlay_prompt
    prompts["debug_overlay_prompt"] = debug_overlay_prompt
    record_profile(pipeline_profile, "prompts_ms", stage_start)

    stage_start = time.perf_counter()
    degradation_reasons = finalize_degradation_reasons(diagnostics)
    result: PipelineResult = {
        "schema_version": SCHEMA_VERSION,
        "degraded": bool(diagnostics["degraded"]),
        "degradation_reasons": degradation_reasons,
        "host_capabilities": normalized_payload.get("host_capabilities", {}),
        "cli_options": {
            "include_raw_emotion": bool(normalized_payload.get(CLI_RAW_EMOTION_REQUEST_KEY)),
        },
        "profile_state": profile_state,
        "memory_update": memory_update,
        "constraint_signals": constraint_signals,
        "weight_schedule": weight_schedule,
        "collection_stack": collection_stack,
        "consistency_snapshot": consistency_snapshot,
        "review_plan": posthoc_plan,
        "posthoc_plan": posthoc_plan,
        "review_shadow": posthoc_shadow,
        "posthoc_shadow": posthoc_shadow,
        "features": features,
        "initial_screen": screen,
        "confirmed_state": confirmed,
        "prediction": prediction,
        "analysis": analysis,
        "routing": routing,
        "route_reasons": route_reasons,
        "response_constraints": response_constraints,
        "state_delta": state_delta,
        "satisfaction_lock": satisfaction_lock,
        "guidance": guidance,
        "overlay_prompt": overlay_prompt,
        "debug_overlay_prompt": debug_overlay_prompt,
        "prompts": prompts,
    }
    record_profile(pipeline_profile, "finalize_ms", stage_start)
    if pipeline_profile is not None:
        pipeline_profile["total_ms"] = round((time.perf_counter() - total_start) * 1000.0, 3)
        result["pipeline_profile"] = pipeline_profile
    LOGGER.info(
        "pipeline mode=%s labels=%s route_reasons=%s degraded=%s total_ms=%.3f",
        confirmed["dominant_mode"],
        ",".join(confirmed["labels"]),
        ",".join(route_reasons),
        result["degraded"],
        (time.perf_counter() - total_start) * 1000.0,
    )
    return result


def parse_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if args.input:
        payload.update(require_json_object(load_json_file(args.input) or {}, f"--input {args.input}"))
    elif not sys.stdin.isatty():
        stdin_text = sys.stdin.read().strip()
        if stdin_text:
            payload.update(require_json_object(json.loads(stdin_text), "stdin"))
    if args.message:
        payload["message"] = args.message
    if args.history_file:
        payload["history"] = load_json_file(args.history_file)
    if args.runtime_file:
        payload["runtime"] = load_json_file(args.runtime_file)
    if args.state_file:
        payload["last_state"] = load_json_file(args.state_file)
    if args.llm_file:
        payload["llm_semantic"] = load_json_file(args.llm_file)
    if getattr(args, "review_file", None):
        payload["review_semantic"] = load_json_file(args.review_file)
    if getattr(args, "posthoc_file", None):
        legacy_review = load_json_file(args.posthoc_file)
        payload["posthoc_semantic"] = legacy_review
        payload.setdefault("review_semantic", legacy_review)
    if getattr(args, "calibration_file", None):
        payload["calibration_state"] = load_json_file(args.calibration_file)
    if getattr(args, "include_raw_emotion", False):
        payload[CLI_RAW_EMOTION_REQUEST_KEY] = True
    return payload


def select_output(command: str, full: dict[str, Any]) -> Any:
    contract = {
        "schema_version": full["schema_version"],
        "degraded": full["degraded"],
        "degradation_reasons": full["degradation_reasons"],
    }
    if command == "host":
        return build_host_output(full)
    if command == "screen":
        return {**contract, "features": full["features"], "initial_screen": full["initial_screen"]}
    if command == "confirm":
        return {**contract, "confirmed_state": full["confirmed_state"], "weight_schedule": full["weight_schedule"], "consistency_snapshot": full["consistency_snapshot"]}
    if command == "predict":
        return {**contract, "prediction": full["prediction"], "analysis": full["analysis"]}
    if command == "route":
        return {**contract, "routing": full["routing"]}
    if command == "guide":
        return {**contract, "guidance": full["guidance"]}
    if command == "posthoc":
        return {
            **contract,
            "collection_stack": full["collection_stack"],
            "review_plan": full["review_plan"],
            "posthoc_plan": full["posthoc_plan"],
            "review_shadow": full["review_shadow"],
            "posthoc_shadow": full["posthoc_shadow"],
            "weight_schedule": full["weight_schedule"],
            "consistency_snapshot": full["consistency_snapshot"],
            "review_pass_prompt": full["prompts"]["review_pass_prompt"],
            "posthoc_reflection_prompt": full["prompts"]["posthoc_reflection_prompt"],
        }
    if command == "overlay":
        return {**contract, "overlay_prompt": full["overlay_prompt"], "debug_overlay_prompt": full["debug_overlay_prompt"]}
    return full


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emotion-aware routing and prompt overlay engine.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("host", "screen", "confirm", "predict", "route", "guide", "posthoc", "overlay", "run"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--input", help="Path to a JSON payload.")
        sub.add_argument("--message", help="Latest user message.")
        sub.add_argument("--history-file", help="Path to history JSON.")
        sub.add_argument("--runtime-file", help="Path to runtime JSON.")
        sub.add_argument("--state-file", help="Path to last_state JSON.")
        sub.add_argument("--llm-file", help="Path to llm_semantic JSON.")
        sub.add_argument("--review-file", help="Path to review_semantic JSON.")
        sub.add_argument("--posthoc-file", help="Path to posthoc_semantic JSON.")
        sub.add_argument("--calibration-file", help="Path to calibration_state JSON.")
        sub.add_argument("--include-raw-emotion", action="store_true", help="Include internal raw affect diagnostics in host output.")
        sub.add_argument("--profile", action="store_true", help="Include pipeline stage timings in full run output.")
        sub.add_argument("--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="WARNING", help="Write runtime logs to stderr.")
        sub.add_argument("--output", help="Path to write JSON output.")
        sub.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    configure_logging(args.log_level)
    try:
        payload = parse_payload(args)
    except FileNotFoundError as exc:
        parser.exit(2, f"{exc}\n")
    except json.JSONDecodeError as exc:
        parser.exit(2, f"Invalid JSON input: {exc}\n")
    except ValueError as exc:
        parser.exit(2, f"{exc}\n")
    if not payload.get("message"):
        parser.error("A message is required via --message, --input, or stdin JSON.")
    full = run_pipeline(payload, profile=args.profile)
    selected = select_output(args.command, full)
    rendered = dump_json(selected, args.pretty)
    if args.output:
        try:
            atomic_write_text(Path(args.output), rendered)
        except OSError as exc:
            parser.exit(2, f"Could not write output {args.output}: {exc}\n")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
