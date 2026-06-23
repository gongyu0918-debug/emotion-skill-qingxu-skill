from __future__ import annotations

from typing import Any

from emotion_scoring import build_emotionality_metrics
from emotion_types import *
from emotion_utils import *


def predict_state(features: dict[str, Any], confirmed: dict[str, Any]) -> dict[str, Any]:
    vector = confirmed["vector"]
    emotion_vector = confirmed["emotion_vector"]
    mode = confirmed["dominant_mode"]
    complexity_score = clamp(
        0.14 * clamp(features["chars"] / 280.0)
        + 0.14 * features["technical_ratio"]
        + 0.1 * clamp(features["file_refs"] / 3.0)
        + 0.1 * clamp(features["list_markers"] / 4.0)
        + 0.08 * clamp(features["questions"] / 3.0)
        + 0.18 * clamp(features["unresolved_turns"] / 5.0)
        + 0.12 * clamp(features["bug_retries"] / 3.0)
        + 0.08 * clamp(features["task_age_minutes"] / 60.0)
        + 0.06 * clamp(features["same_issue_mentions"] / 3.0)
        + 0.08 * features["stall_ratio"]
        + 0.06 * clamp(features["code_markers"])
    )
    complexity_level = "high" if complexity_score >= 0.68 else "medium" if complexity_score >= 0.4 else "low"
    frustration_risk = clamp(0.3 * emotion_vector["frustration"] + 0.18 * emotion_vector["urgency"] + 0.18 * features["delay_pressure"] + 0.14 * features["stuck_pressure"] + 0.1 * features["stall_ratio"] + 0.06 * features["resolution_mismatch"] + 0.08 * complexity_score - 0.08 * emotion_vector["satisfaction"])
    stall_risk = clamp(0.26 * complexity_score + 0.18 * features["delay_pressure"] + 0.16 * features["background_pressure"] + 0.2 * features["stuck_pressure"] + 0.1 * features["stall_ratio"] + 0.1 * emotion_vector["confusion"])
    if emotion_vector["urgency"] >= 0.78 or frustration_risk >= 0.78:
        patience_window_sec = 15
    elif frustration_risk >= 0.65:
        patience_window_sec = 25
    elif complexity_score >= 0.6:
        patience_window_sec = 45
    else:
        patience_window_sec = 60
    if frustration_risk >= 0.75:
        next_update_deadline_sec = 10
    elif stall_risk >= 0.7 or mode in {"urgent", "frustrated"}:
        next_update_deadline_sec = 15
    elif mode == "skeptical":
        next_update_deadline_sec = 20
    elif complexity_score >= 0.65:
        next_update_deadline_sec = 25
    else:
        next_update_deadline_sec = 40
    low_clarity = emotion_vector["confusion"] >= 0.58 and features["goal_specificity"] < 0.42
    probe_needed = bool(low_clarity or (mode == "confused" and features["questions"] >= 1) or (frustration_risk >= 0.72 and features["anger_hits"] == 0 and features["goal_specificity"] < 0.34))
    if mode in {"urgent", "frustrated", "skeptical"} and features["goal_specificity"] >= 0.34:
        probe_needed = False
    if features["evidence_request"] >= 1.0 or features["comparison_request"] >= 1.0 or features["guardrail_request"] >= 1.0:
        probe_needed = False
    reasons: list[str] = []
    if features["technical_hits"]:
        reasons.append("technical density")
    if features["file_refs"]:
        reasons.append("file or API references")
    if features["unresolved_turns"] >= 2:
        reasons.append("multiple unresolved turns")
    if features["bug_retries"] >= 1:
        reasons.append("repeat bug retries")
    if features["stall_hits"] >= 1:
        reasons.append("stall or hang wording")
    return {
        "task_complexity": {"score": round(complexity_score, 4), "level": complexity_level, "reasons": reasons},
        "frustration_risk": round(frustration_risk, 4),
        "stall_risk": round(stall_risk, 4),
        "patience_window_sec": patience_window_sec,
        "next_update_deadline_sec": next_update_deadline_sec,
        "probe_needed": probe_needed,
        "guard_needed": bool((vector["satisfaction"] >= 0.62 and vector["frustration"] <= 0.4) or features["guard_ratio"] >= 0.34),
    }


def build_analysis_plan(features: dict[str, Any], screen: dict[str, Any], confirmed: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    mode = confirmed["dominant_mode"]
    ambiguity = clamp((1.0 - confirmed["vector"]["clarity"]) * 0.48 + 0.2 * features["vague_ratio"] + 0.16 * features["question_density"] + 0.12 * features["contradiction_signal"] - 0.14 * features["goal_specificity"] - 0.1 * screen["confidence"] - 0.08 * features["evidence_request"] - 0.08 * features["comparison_request"] - 0.08 * features["guardrail_request"])
    strong_state = screen["confidence"] >= 0.62 and ambiguity <= 0.22 and len([label for label in confirmed["labels"] if label != "neutral"]) <= 2
    semantic_pass = "fast" if mode in {"cautious", "confused", "skeptical"} or not strong_state else "skip"
    if semantic_pass == "skip":
        target_ms, max_response_tokens, max_prompt_chars = 0, 0, 260
    elif mode in {"urgent", "frustrated"}:
        target_ms, max_response_tokens, max_prompt_chars = 350, 90, 420
    else:
        target_ms, max_response_tokens, max_prompt_chars = 500, 120, 520
    return {
        "semantic_pass": semantic_pass,
        "ambiguity": round(ambiguity, 4),
        "target_ms": target_ms,
        "max_prompt_chars": max_prompt_chars,
        "max_response_tokens": max_response_tokens,
        "compact_overlay_chars": 220,
        "state_prompt_mode": "compact",
        "skip_probe": bool(mode in {"urgent", "frustrated", "skeptical"} and features["goal_specificity"] >= 0.34),
        "priority_reason": screen["evidence"][:3],
    }


def build_profile_state(features: dict[str, Any]) -> dict[str, Any]:
    profile = features["user_profile"]
    return {
        "id": profile["id"],
        "timezone": profile["timezone"],
        "local_hour": profile["local_hour"],
        "in_work_window": profile["in_work_window"],
        "work_hours_local": profile["work_hours_local"],
        "baseline": profile["baseline"],
        "persona_traits": profile["persona_traits"],
        "persona_source": profile["persona_source"],
        "affective_prior": profile["affective_prior"],
        "affective_prior_source": profile["affective_prior_source"],
        "affective_prior_weight": profile["affective_prior_weight"],
        "effective_delay_budget_seconds": features["effective_delay_budget_seconds"],
        "style_shift": {
            "politeness_delta": features["politeness_delta"],
            "terseness_delta": features["terseness_delta"],
            "punctuation_delta": features["punctuation_delta"],
            "directness_delta": features["directness_delta"],
        },
    }


def build_memory_update(payload: dict[str, Any], features: dict[str, Any], confirmed: dict[str, Any], weight_schedule: dict[str, Any], consistency_snapshot: dict[str, Any]) -> dict[str, Any]:
    baseline = features["user_profile"]["baseline"]
    persona_traits = features["user_profile"]["persona_traits"]
    affective_prior = features["user_profile"]["affective_prior"]
    emotion_vector = confirmed["emotion_vector"]
    calibration = payload.get("calibration_state") or {}
    calm_factor = clamp(1.0 - max(emotion_vector["urgency"], emotion_vector["frustration"]))
    learning_rate = round(clamp(0.03 + 0.11 * confirmed["confidence"] * calm_factor, 0.03, 0.12), 4)
    observed_delay = baseline["response_delay_seconds"]
    if features["response_delay_seconds"] > 0:
        if emotion_vector["urgency"] >= 0.55 or emotion_vector["frustration"] >= 0.55:
            observed_delay = max(8.0, min(baseline["response_delay_seconds"], features["response_delay_seconds"]))
        elif emotion_vector["satisfaction"] >= 0.45 or emotion_vector["confusion"] <= 0.4:
            observed_delay = min(120.0, max(baseline["response_delay_seconds"], features["response_delay_seconds"]))
    observed_style = {
        "response_delay_seconds": round(float(observed_delay), 2),
        "politeness": round(features["polite_ratio"], 4),
        "terseness": round(features["short_burst"], 4),
        "punctuation": round(features["punctuation_pressure"], 4),
        "directness": round(features["command_ratio"], 4),
    }
    proposed_baseline = {
        key: round((1.0 - learning_rate) * float(baseline[key]) + learning_rate * float(observed_style[key]), 4)
        for key in observed_style
    }
    observed_persona = {
        "patience": round(clamp(1.0 - max(emotion_vector["urgency"], emotion_vector["frustration"])), 4),
        "skepticism": round(clamp(max(emotion_vector["skepticism"], features["skepticism_ratio"])), 4),
        "caution": round(clamp(max(emotion_vector["cautiousness"], features["assurance_ratio"])), 4),
        "openness": round(clamp(emotion_vector["openness"]), 4),
        "assertiveness": round(clamp(features["command_ratio"]), 4),
    }
    persona_learning_rate = round(clamp(learning_rate * 0.55, 0.02, 0.07), 4)
    proposed_persona_traits = {
        key: round((1.0 - persona_learning_rate) * float(persona_traits[key]) + persona_learning_rate * float(observed_persona[key]), 4)
        for key in observed_persona
    }
    prior_learning_rate = round(clamp(persona_learning_rate * 0.6, 0.015, 0.045), 4)
    proposed_affective_prior = {
        key: round((1.0 - prior_learning_rate) * float(affective_prior.get(key, 0.0)) + prior_learning_rate * float(emotion_vector[key]), 4)
        for key in EMOTION_DIMS
    }
    calibration_learning_rate = round(clamp(0.05 + 0.08 * confirmed["confidence"], 0.05, 0.12), 4)
    prior_consistency = clamp(safe_float(calibration.get("consistency_rate"), weight_schedule["effective_consistency"]))
    prior_prediction_agreement = clamp(safe_float(calibration.get("prediction_agreement"), weight_schedule["effective_consistency"]))
    prior_observed_turns = safe_int(calibration.get("observed_turns"), 0)
    prior_posthoc_samples = safe_int(calibration.get("posthoc_samples"), 0)
    prior_consistency_samples = safe_int(calibration.get("consistency_samples"), prior_posthoc_samples)
    prior_stable_hits = safe_int(calibration.get("stable_prediction_hits"), 0)
    if consistency_snapshot["available"]:
        proposed_consistency_rate = round((1.0 - calibration_learning_rate) * prior_consistency + calibration_learning_rate * consistency_snapshot["consistency_rate"], 4)
        proposed_prediction_agreement = round((1.0 - calibration_learning_rate) * prior_prediction_agreement + calibration_learning_rate * consistency_snapshot["vector_alignment"], 4)
    else:
        proposed_consistency_rate = round(prior_consistency, 4)
        proposed_prediction_agreement = round((1.0 - calibration_learning_rate) * prior_prediction_agreement + calibration_learning_rate * confirmed["confidence"], 4)
    stable_hit_increment = 1 if consistency_snapshot["available"] and consistency_snapshot["consistency_rate"] >= 0.72 else 0
    proposed_calibration_state = {
        "observed_turns": prior_observed_turns + 1,
        "posthoc_samples": prior_posthoc_samples + (1 if consistency_snapshot["available"] else 0),
        "consistency_samples": prior_consistency_samples + (1 if consistency_snapshot["available"] else 0),
        "stable_prediction_hits": prior_stable_hits + stable_hit_increment,
        "prediction_agreement": proposed_prediction_agreement,
        "consistency_rate": proposed_consistency_rate,
    }
    return {
        "host_profile_update_recommended": bool(confirmed["confidence"] >= 0.58),
        "should_persist": bool(confirmed["confidence"] >= 0.58),
        "learning_rate": learning_rate,
        "persona_learning_rate": persona_learning_rate,
        "prior_learning_rate": prior_learning_rate,
        "calibration_learning_rate": calibration_learning_rate,
        "observed_style": observed_style,
        "observed_persona": observed_persona,
        "proposed_baseline": proposed_baseline,
        "proposed_persona_traits": proposed_persona_traits,
        "proposed_affective_prior": proposed_affective_prior,
        "proposed_calibration_state": proposed_calibration_state,
        "notes": [
            "use EMA merge into the host-owned baseline profile",
            "merge persona traits with a smaller EMA weight",
            "keep affective prior slower than persona traits",
            "keep front or review-pass trust tied to long-run consistency",
            "high-pressure turns keep a lower learning weight",
        ],
    }


def build_routing(features: FeatureMap, confirmed: ConfirmedState, prediction: dict[str, Any]) -> RoutingState:
    mode = confirmed["dominant_mode"]
    vector = confirmed["vector"]
    emotion_vector = confirmed["emotion_vector"]
    labels = set(confirmed.get("labels") or [])
    frustration_risk = prediction["frustration_risk"]
    stall_risk = prediction["stall_risk"]
    complexity = prediction["task_complexity"]["score"]
    skeptical_priority = bool(
        (mode == "skeptical" or "skeptical" in labels)
        and (
            emotion_vector["skepticism"] >= 0.32
            or features["speculation_ratio"] >= 0.25
            or features["skepticism_ratio"] >= 0.25
            or features["context_loss_ratio"] >= 0.25
            or features["execution_plumbing_ratio"] >= 0.25
        )
        and (
            features["contradiction_signal"] >= 0.24
            or features["resolution_mismatch"] >= 0.28
            or features["speculation_ratio"] >= 0.25
            or features["context_loss_ratio"] >= 0.25
            or features["execution_plumbing_ratio"] >= 0.25
            or features["same_issue_mentions"] >= 1
            or features["assurance_ratio"] >= 0.25
            or features["stuck_pressure"] >= 0.72
            or features["delay_pressure"] >= 0.42
        )
    )
    if emotion_vector["urgency"] >= 0.88 and emotion_vector["frustration"] >= 0.74:
        queue_mode = "interrupt"
    elif mode in {"urgent", "frustrated"} or skeptical_priority or emotion_vector["urgency"] >= 0.64 or emotion_vector["frustration"] >= 0.62 or stall_risk >= 0.68:
        queue_mode = "steer"
    else:
        queue_mode = "collect"
    prefer_main_thread = bool(mode in {"urgent", "frustrated"} or skeptical_priority or emotion_vector["urgency"] >= 0.56 or emotion_vector["frustration"] >= 0.54 or emotion_vector["confusion"] >= 0.62 or emotion_vector["skepticism"] >= 0.58 or vector["clarity"] <= 0.4 or stall_risk >= 0.62 or features["delay_pressure"] >= 0.6)
    defer_heartbeat = bool(prefer_main_thread or mode in {"urgent", "frustrated"} or frustration_risk >= 0.62 or stall_risk >= 0.62)
    allow_parallel = bool(complexity >= 0.72 and not prefer_main_thread and mode in {"exploratory", "neutral"})
    progress_interval = 10 if frustration_risk >= 0.75 else 15 if mode in {"urgent", "frustrated"} or skeptical_priority or stall_risk >= 0.68 else 20 if complexity >= 0.62 or mode in {"skeptical", "cautious"} or features["guardrail_request"] >= 1.0 else 35
    if mode == "urgent":
        reply_style, verification_level, hermes_personality = "act_then_brief", "high", "concise"
    elif mode == "frustrated":
        reply_style, verification_level, hermes_personality = "repair_then_explain", "high", "concise"
    elif mode == "confused":
        reply_style, verification_level, hermes_personality = "explain_then_act", "high" if features["evidence_request"] >= 1.0 or features["unresolved_turns"] >= 2 or features["same_issue_mentions"] >= 1 else "medium", "teacher"
    elif mode == "skeptical":
        reply_style, verification_level, hermes_personality = "evidence_then_act", "very_high" if skeptical_priority else "high", "analytical"
    elif mode == "satisfied":
        reply_style, verification_level, hermes_personality = "guard_then_close", "high", "helpful"
    elif mode == "cautious":
        reply_style, verification_level, hermes_personality = "verify_then_act", "very_high", "careful"
    else:
        reply_style, verification_level, hermes_personality = "synthesize_then_recommend", "medium", "helpful"
    return {
        "reply_style": reply_style,
        "verification_level": verification_level,
        "thread_interface": {
            "queue_mode": queue_mode,
            "prefer_main_thread": prefer_main_thread,
            "defer_heartbeat": defer_heartbeat,
            "allow_parallel_subagents": allow_parallel,
            "max_parallel_subagents": 2 if allow_parallel else 0 if prefer_main_thread else 1,
            "progress_update_interval_sec": progress_interval,
            "openclaw": {
                "queue_mode": queue_mode,
                "prefer_lane": "main",
                "defer_heartbeat": defer_heartbeat,
                "allow_sessions_spawn": bool(allow_parallel or (complexity >= 0.58 and not prefer_main_thread)),
                "use_sessions_yield": bool(allow_parallel and complexity >= 0.78),
            },
            "hermes": {
                "personality": hermes_personality,
                "busy_input_mode": "interrupt" if mode in {"urgent", "frustrated"} or queue_mode in {"interrupt", "steer"} else "queue",
                "suggested_overlay_scope": "turn-local",
            },
        },
    }


def has_vector_signal(raw: Any, dims: tuple[str, ...]) -> bool:
    return isinstance(raw, dict) and any(dim in raw and raw.get(dim) is not None for dim in dims)


def significant_vector_delta(current: dict[str, Any], previous: dict[str, Any], dims: tuple[str, ...], floor: float = 0.05) -> dict[str, float]:
    deltas: dict[str, float] = {}
    for dim in dims:
        try:
            delta = safe_float(current.get(dim), 0.0) - safe_float(previous.get(dim), 0.0)
        except (TypeError, ValueError):
            continue
        rounded = round(delta, 4)
        if abs(rounded) >= floor:
            deltas[dim] = rounded
    return deltas


def build_state_delta(payload: dict[str, Any], confirmed: dict[str, Any]) -> dict[str, Any]:
    last_state = payload.get("last_state") or {}
    previous_vector_raw = last_state.get("vector") if isinstance(last_state, dict) else {}
    previous_emotion_raw = last_state.get("emotion_vector") if isinstance(last_state, dict) else {}
    has_interaction = has_vector_signal(previous_vector_raw, STATE_DIMS)
    has_emotion = has_vector_signal(previous_emotion_raw, EMOTION_DIMS)
    if not has_interaction and not has_emotion:
        return {
            "available": False,
            "dominant_shift": "new_turn",
            "emotion": {},
            "interaction": {},
        }

    previous_vector = clamp_dict(previous_vector_raw, STATE_DIMS)
    previous_emotion = clamp_dict(previous_emotion_raw, EMOTION_DIMS)
    interaction_delta = significant_vector_delta(confirmed["vector"], previous_vector, INTERACTION_DIMS)
    emotion_delta = significant_vector_delta(confirmed["emotion_vector"], previous_emotion, EMOTION_DIMS)
    if emotion_delta.get("frustration", 0.0) >= 0.12:
        dominant_shift = "needs_concrete_unblock"
    elif emotion_delta.get("urgency", 0.0) >= 0.12:
        dominant_shift = "needs_priority_action"
    elif emotion_delta.get("skepticism", 0.0) >= 0.12 or interaction_delta.get("trust", 0.0) <= -0.12:
        dominant_shift = "needs_evidence_first"
    elif emotion_delta.get("confusion", 0.0) >= 0.12 or interaction_delta.get("clarity", 0.0) <= -0.12:
        dominant_shift = "needs_alignment_check"
    elif emotion_delta.get("satisfaction", 0.0) >= 0.12:
        dominant_shift = "ready_for_closeout"
    elif emotion_delta.get("satisfaction", 0.0) <= -0.12:
        dominant_shift = "needs_stabilization"
    elif not interaction_delta and not emotion_delta:
        dominant_shift = "stable"
    else:
        dominant_shift = "changed"
    return {
        "available": True,
        "dominant_shift": dominant_shift,
        "emotion": emotion_delta,
        "interaction": interaction_delta,
    }


def validate_route_reasons(reasons: list[str], diagnostics: dict[str, Any] | None = None) -> list[str]:
    valid: list[str] = []
    for reason in unique_labels(reasons):
        if reason in ROUTE_REASON_ENUM:
            valid.append(reason)
    if len(valid) > MAX_ROUTE_REASONS and diagnostics is not None:
        mark_degraded(diagnostics, "route_reasons_truncated")
    return valid[:MAX_ROUTE_REASONS]


def build_route_reasons(
    features: FeatureMap,
    confirmed: ConfirmedState,
    prediction: dict[str, Any],
    routing: RoutingState,
    state_delta: dict[str, Any],
    diagnostics: dict[str, Any] | None = None,
) -> list[str]:
    mode = confirmed["dominant_mode"]
    labels = set(confirmed.get("labels") or [])
    emotion_vector = confirmed["emotion_vector"]
    reasons: list[str] = []
    if routing["thread_interface"]["queue_mode"] in {"steer", "interrupt"}:
        reasons.append("runtime_priority")
    if mode == "urgent" or emotion_vector["urgency"] >= 0.64 or features.get("delay_pressure", 0.0) >= 0.42:
        reasons.append("urgent_pressure")
    if mode == "frustrated" or prediction["frustration_risk"] >= 0.62 or features.get("bug_retries", 0.0) >= 1:
        reasons.append("repeat_failure_pressure")
    if mode == "skeptical" or "skeptical" in labels or features.get("evidence_request", 0.0) >= 1.0:
        reasons.append("evidence_requested")
    if mode == "cautious" or "cautious" in labels or features.get("guardrail_request", 0.0) >= 1.0:
        reasons.append("scope_guard_requested")
    if mode == "confused" or emotion_vector["confusion"] >= 0.58:
        reasons.append("low_clarity")
    if mode == "satisfied" or prediction["guard_needed"]:
        reasons.append("post_success_guard")
    if prediction["stall_risk"] >= 0.62 or features.get("stall_ratio", 0.0) >= 0.25:
        reasons.append("stall_risk")
    if state_delta.get("dominant_shift") in {"needs_concrete_unblock", "needs_evidence_first", "needs_alignment_check", "needs_stabilization", "needs_priority_action"}:
        reasons.append(str(state_delta["dominant_shift"]))
    if features.get("goal_specificity", 0.0) >= 0.48:
        reasons.append("task_specific")
    return validate_route_reasons(reasons, diagnostics)


def build_satisfaction_lock(features: dict[str, Any], confirmed: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    mode = confirmed["dominant_mode"]
    emotion_vector = confirmed["emotion_vector"]
    active = bool(mode == "satisfied" or prediction["guard_needed"] or features.get("success_ratio", 0.0) >= 0.34)
    if not active:
        return {
            "active": False,
            "reason": "inactive",
            "allowed_actions": [],
            "blocked_actions": [],
        }
    if features.get("guard_ratio", 0.0) >= 0.34:
        reason = "post_success_guard"
    elif emotion_vector["satisfaction"] >= 0.5:
        reason = "user_satisfied"
    elif features.get("resolution_claimed", 0.0) >= 1.0:
        reason = "resolution_claimed"
    else:
        reason = "guard_needed"
    return {
        "active": True,
        "reason": reason,
        "allowed_actions": ["summarize_result", "run_regression_check", "prepare_handoff"],
        "blocked_actions": ["expand_scope", "start_new_refactor", "change_config_without_request"],
    }


def build_response_constraints(
    confirmed: dict[str, Any],
    routing: dict[str, Any],
    prediction: dict[str, Any],
    satisfaction_lock: dict[str, Any],
) -> list[str]:
    mode = confirmed["dominant_mode"]
    constraints: list[str] = []
    if mode == "urgent":
        constraints.extend(["lead_with_action", "keep_first_reply_short", "progress_update_required"])
    elif mode == "frustrated":
        constraints.extend(["repair_before_explain", "avoid_repeating_failed_path", "progress_update_required"])
    elif mode == "skeptical":
        constraints.extend(["show_basis_first", "name_verification_steps", "avoid_guessing"])
    elif mode == "cautious":
        constraints.extend(["verify_before_editing", "keep_scope_tight", "protect_user_boundaries"])
    elif mode == "confused":
        constraints.extend(["explain_next_step", "ask_at_most_one_question"])
    elif mode == "satisfied":
        constraints.extend(["guard_mode", "avoid_scope_expansion", "close_with_regression_check"])
    else:
        constraints.extend(["state_recommendation_first", "expand_only_when_useful"])
    if routing["verification_level"] in {"high", "very_high"}:
        constraints.append("include_check_result")
    if prediction["next_update_deadline_sec"] <= 20:
        constraints.append("progress_update_required")
    if satisfaction_lock["active"]:
        constraints.extend(["avoid_scope_expansion", "close_with_regression_check"])
    return unique_labels(constraints)[:8]
