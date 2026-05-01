from __future__ import annotations

from typing import Any, Callable, NamedTuple

from emotion_features import load_review_semantic
from emotion_types import *
from emotion_utils import *


class DominantModeRule(NamedTuple):
    rule_id: str
    mode: str
    predicate: Callable[[], bool]


def derive_emotion_vector(state_vector: dict[str, float], features: dict[str, Any]) -> dict[str, float]:
    confusion = clamp(
        0.48 * (1.0 - state_vector["clarity"])
        + 0.12 * clamp(features["confusion_hits"] / 2.0)
        + 0.14 * features["explicit_confusion_request"]
        + 0.05 * features["vague_ratio"]
        + 0.04 * clamp(features["questions"] / 3.0)
        - 0.08 * state_vector["urgency"]
        - 0.06 * state_vector["frustration"]
        - 0.1 * features["skepticism_ratio"]
        + 0.06 * features["hedge_ratio"]
        - 0.12 * features["speculation_ratio"]
        - 0.08 * features["context_loss_ratio"]
        - 0.08 * features["execution_plumbing_ratio"]
        - 0.06 * features["contradiction_signal"]
        - 0.08 * features["goal_specificity"]
        - 0.05 * features["task_object_ratio"]
        - 0.08 * features["evidence_request"]
        - 0.08 * features["comparison_request"]
        - 0.08 * features["guardrail_request"]
    )
    skepticism = clamp(
        0.46 * features["skepticism_ratio"]
        + 0.24 * features["speculation_ratio"]
        + 0.14 * features["context_loss_ratio"]
        + 0.18 * features["execution_plumbing_ratio"]
        + 0.08 * features["hedge_ratio"]
        + 0.16 * features["resolution_mismatch"]
        + 0.14 * features["contradiction_signal"]
        + 0.1 * features["soft_correction"]
        + 0.08 * features["question_density"]
        + 0.06 * features["assurance_ratio"]
        + 0.06 * (1.0 - state_vector["trust"])
        + 0.06 * features["stuck_pressure"]
        + 0.04 * features["goal_specificity"]
        + 0.05 * features["dismissive_pressure"]
        + 0.03 * features["tempo_pause_pressure"]
        + 0.24 * features["evidence_request"]
    )
    cautiousness = clamp(
        0.48 * features["caution_ratio"]
        + 0.28 * features["boundary_ratio"]
        + 0.18 * features["assurance_ratio"]
        + 0.08 * state_vector["trust"]
        + 0.06 * features["polite_ratio"]
        + 0.22 * features["guardrail_request"]
    )
    openness = clamp(
        0.68 * features["explore_ratio"]
        + 0.16 * state_vector["engagement"]
        + 0.06 * clamp(features["questions"] / 3.0)
        + 0.28 * features["comparison_request"]
        - 0.1 * state_vector["urgency"]
        - 0.08 * state_vector["frustration"]
    )
    return {
        "urgency": round(clamp(state_vector["urgency"]), 4),
        "frustration": round(clamp(state_vector["frustration"]), 4),
        "confusion": round(confusion, 4),
        "skepticism": round(skepticism, 4),
        "satisfaction": round(clamp(state_vector["satisfaction"]), 4),
        "cautiousness": round(cautiousness, 4),
        "openness": round(openness, 4),
    }


def build_interaction_state(state_vector: dict[str, float]) -> dict[str, float]:
    return {
        "clarity": round(clamp(state_vector["clarity"]), 4),
        "trust": round(clamp(state_vector["trust"]), 4),
        "engagement": round(clamp(state_vector["engagement"]), 4),
    }


def build_mode_scores(emotion_vector: dict[str, float], features: dict[str, Any]) -> dict[str, float]:
    return {
        "urgent": round(clamp(emotion_vector["urgency"] * 1.04 + 0.08 * features["delay_pressure"] + 0.1 * features["blocking_ratio"] + 0.08 * features["missed_expectation_ratio"] + 0.06 * features["typing_chaos"] + 0.05 * features["textism_pressure"] + 0.04 * features["command_ratio"] + 0.04 * features["directness_delta"] + 0.08 * features["stall_ratio"] + 0.04 * features["tempo_pause_pressure"] + 0.04 * features["execution_plumbing_ratio"] + 0.04 * clamp(features["same_issue_mentions"] / 3.0) - 0.03 * features["evidence_request"] - 0.04 * features["guardrail_request"]), 4),
        "frustrated": round(clamp(emotion_vector["frustration"] * 1.14 + 0.12 * features["stuck_pressure"] + 0.08 * features["missed_expectation_ratio"] + 0.08 * features["context_loss_ratio"] + 0.08 * features["execution_plumbing_ratio"] + 0.08 * features["stall_ratio"] + 0.06 * features["resolution_mismatch"] + 0.08 * features["abrupt_delta"] + 0.06 * features["delay_pressure"] + 0.08 * features["dismissive_pressure"] + 0.04 * features["tempo_pause_pressure"] + 0.06 * features["contradiction_signal"] + 0.04 * features["soft_correction"] + 0.04 * features["guardrail_request"]), 4),
        "confused": round(clamp(emotion_vector["confusion"] * 0.92 + 0.06 * clamp(features["confusion_hits"] / 2.0) + 0.1 * features["explicit_confusion_request"] + 0.08 * features["explicit_confusion_request"] * features["evidence_request"] + 0.03 * features["vague_ratio"] - 0.1 * features["goal_specificity"] - 0.12 * features["speculation_ratio"] - 0.08 * features["context_loss_ratio"] - 0.08 * features["execution_plumbing_ratio"] - 0.06 * features["contradiction_signal"] - 0.08 * features["evidence_request"] - 0.08 * features["comparison_request"] - 0.08 * features["guardrail_request"]), 4),
        "skeptical": round(clamp(emotion_vector["skepticism"] * 1.08 + 0.12 * features["speculation_ratio"] + 0.08 * features["context_loss_ratio"] + 0.1 * features["execution_plumbing_ratio"] + 0.08 * features["resolution_mismatch"] + 0.06 * features["contradiction_signal"] + 0.06 * features["stuck_pressure"] + 0.04 * features["delay_pressure"] + 0.04 * features["goal_specificity"] + 0.05 * features["dismissive_pressure"] + 0.18 * features["evidence_request"]), 4),
        "satisfied": round(clamp(emotion_vector["satisfaction"] + 0.1 * features["guard_ratio"] + 0.08 * features["success_ratio"] + 0.08 * features["continue_ratio"] + 0.06 * features["resolution_claimed"]), 4),
        "cautious": round(clamp(emotion_vector["cautiousness"] * 1.1 + 0.06 * features["goal_specificity"] + 0.04 * features["polite_ratio"] + 0.08 * features["assurance_ratio"] + 0.06 * features["boundary_ratio"] + 0.06 * features["context_loss_ratio"] + 0.04 * features["contradiction_signal"] + 0.16 * features["guardrail_request"]), 4),
        "exploratory": round(clamp(emotion_vector["openness"] * 1.08 + 0.06 * features["explore_ratio"] + 0.04 * features["technical_ratio"] + 0.22 * features["comparison_request"] + 0.04 * features["goal_specificity"]), 4),
        "neutral": 0.22,
    }


def build_intensity_profile(emotion_vector: dict[str, float]) -> dict[str, str]:
    return {dim: intensity_band(score) for dim, score in emotion_vector.items()}


def build_emotion_composition(emotion_vector: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, float(emotion_vector.get(dim, 0.0))) for dim in EMOTION_DIMS)
    if total <= 1e-6:
        return {dim: 0.0 for dim in EMOTION_DIMS}
    return {
        dim: round(clamp(float(emotion_vector.get(dim, 0.0)) / total), 4)
        for dim in EMOTION_DIMS
    }


def build_emotionality_metrics(emotion_vector: dict[str, float], features: dict[str, Any]) -> dict[str, Any]:
    active_values = sorted((float(emotion_vector.get(dim, 0.0)) for dim in EMOTION_DIMS), reverse=True)
    dominant = active_values[0] if active_values else 0.0
    mean_signal = sum(active_values) / max(len(active_values), 1)
    emotionality = clamp(
        0.44 * dominant
        + 0.22 * mean_signal
        + 0.1 * features["punctuation_pressure"]
        + 0.08 * features["delay_pressure"]
        + 0.08 * features["stuck_pressure"]
        + 0.08 * features["skepticism_ratio"]
    )
    composition = build_emotion_composition(emotion_vector)
    top_axes = [
        {"axis": dim, "share": composition[dim], "score": round(float(emotion_vector.get(dim, 0.0)), 4)}
        for dim in sorted(EMOTION_DIMS, key=lambda axis: float(emotion_vector.get(axis, 0.0)), reverse=True)
        if float(emotion_vector.get(dim, 0.0)) >= 0.18
    ][:3]
    return {
        "emotionality": round(emotionality, 4),
        "composition": composition,
        "top_axes": top_axes,
    }


def build_posthoc_shadow(payload: dict[str, Any], features: dict[str, Any], confirmed: dict[str, Any], analysis: dict[str, Any], posthoc_plan: dict[str, Any]) -> dict[str, Any]:
    review_semantic = load_review_semantic(payload)
    source_vector = clamp_dict(review_semantic.get("emotion_vector"), EMOTION_DIMS) if review_semantic.get("emotion_vector") else confirmed["emotion_vector"]
    source_labels = canonicalize_labels(list(review_semantic.get("labels") or [])) if review_semantic.get("labels") else canonicalize_labels(confirmed["labels"])
    metrics = build_emotionality_metrics(source_vector, features)
    dominant_axis = max(EMOTION_DIMS, key=lambda dim: float(source_vector.get(dim, 0.0)))
    available = bool(review_semantic.get("emotion_vector") or review_semantic.get("labels"))
    return {
        "enabled": True,
        "available": available,
        "source": "review_semantic" if available else "confirmed_estimate",
        "is_estimate": not available,
        "mode": "shadow_review",
        "style": posthoc_plan["style"],
        "weight": round(float(posthoc_plan["weight"]), 4),
        "target_ms": int(posthoc_plan["target_ms"]),
        "emotionality": metrics["emotionality"],
        "composition": metrics["composition"],
        "top_axes": metrics["top_axes"],
        "dominant_axis": dominant_axis,
        "dominant_axis_score": round(float(source_vector.get(dominant_axis, 0.0)), 4),
        "labels": source_labels,
        "confidence": round(clamp(float(review_semantic.get("confidence", 0.0) or 0.0)), 4) if available else round(float(confirmed["confidence"]), 4),
        "stance_cues": analysis["priority_reason"][:3],
    }


def build_collection_stack(weight_schedule: dict[str, Any], features: dict[str, Any], posthoc_plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "sources": ["front_prompt", "review_prompt", "history_context", "time_runtime_context"],
        "front_weight": round(float(weight_schedule["screen_weight"]), 4),
        "review_weight": round(float(weight_schedule["posthoc_weight"]), 4),
        "posthoc_weight": round(float(weight_schedule["posthoc_weight"]), 4),
        "history_active": True,
        "time_runtime_active": True,
        "review_mode": posthoc_plan["style"],
        "posthoc_mode": posthoc_plan["style"],
        "consistency_rate": round(float(weight_schedule["consistency_rate"]), 4),
        "effective_consistency": round(float(weight_schedule["effective_consistency"]), 4),
        "response_delay_seconds": float(features["response_delay_seconds"]),
        "effective_delay_budget_seconds": round(float(features["effective_delay_budget_seconds"]), 4),
    }


def build_constraint_signals(features: dict[str, Any]) -> dict[str, float]:
    return {
        "boundary_strength": round(clamp(0.62 * features["boundary_ratio"] + 0.2 * features["caution_ratio"] + 0.18 * features["assurance_ratio"]), 4),
        "verification_preference": round(clamp(0.52 * features["assurance_ratio"] + 0.26 * features["caution_ratio"] + 0.12 * features["boundary_ratio"] + 0.1 * features["goal_specificity"]), 4),
        "scope_tightness": round(clamp(0.74 * features["boundary_ratio"] + 0.16 * features["command_ratio"] + 0.1 * features["goal_specificity"]), 4),
        "evidence_requirement": round(clamp(0.56 * features["skepticism_ratio"] + 0.18 * features["resolution_mismatch"] + 0.14 * features["contradiction_signal"] + 0.12 * features["goal_specificity"]), 4),
    }


def build_weight_schedule(payload: dict[str, Any], features: dict[str, Any]) -> dict[str, Any]:
    calibration = payload.get("calibration_state") or {}
    observed_turns = int(calibration.get("observed_turns", features.get("unresolved_turns", 0)) or 0)
    posthoc_samples = int(calibration.get("posthoc_samples", calibration.get("calibrated_samples", 0)) or 0)
    consistency_samples = int(calibration.get("consistency_samples", posthoc_samples) or 0)
    stable_prediction_hits = int(calibration.get("stable_prediction_hits", 0) or 0)
    prediction_agreement = clamp(float(calibration.get("prediction_agreement", 0.0) or 0.0))
    consistency_rate = clamp(float(calibration.get("consistency_rate", calibration.get("front_posthoc_consistency", prediction_agreement)) or prediction_agreement))
    agreement_confidence = clamp(consistency_samples / 18.0)
    effective_consistency = clamp((consistency_rate * agreement_confidence) + (prediction_agreement * (1.0 - agreement_confidence)))
    profile_seed = features["user_profile"]
    explicit_prior = 1.0 if profile_seed.get("affective_prior_source") == "explicit" else 0.0
    persona_seed = 1.0 if profile_seed.get("persona_source") in {"persona_traits", "big5"} else 0.0
    maturity = clamp(
        0.28 * clamp(posthoc_samples / 24.0)
        + 0.22 * clamp(observed_turns / 30.0)
        + 0.2 * clamp(stable_prediction_hits / 18.0)
        + 0.18 * effective_consistency
        + 0.07 * explicit_prior
        + 0.05 * persona_seed
    )
    if posthoc_samples < 8 or observed_turns < 12:
        stage = "bootstrap"
        base_screen_weight, prior_weight, base_posthoc_weight, carryover_weight = 0.24, 0.08, 0.56, 0.12
    elif maturity < 0.42:
        stage = "calibrating"
        base_screen_weight, prior_weight, base_posthoc_weight, carryover_weight = 0.3, 0.12, 0.44, 0.14
    elif maturity < 0.72:
        stage = "adapting"
        base_screen_weight, prior_weight, base_posthoc_weight, carryover_weight = 0.4, 0.18, 0.28, 0.14
    else:
        stage = "stable"
        base_screen_weight, prior_weight, base_posthoc_weight, carryover_weight = 0.5, 0.22, 0.14, 0.14
    consistency_shift = (effective_consistency - 0.5) * (0.16 if stage in {"bootstrap", "calibrating"} else 0.22)
    screen_weight = round(clamp(base_screen_weight + consistency_shift, 0.18, 0.58), 4)
    posthoc_weight = round(clamp(base_posthoc_weight - consistency_shift, 0.12, 0.62), 4)
    prior_weight = round(prior_weight, 4)
    carryover_weight = round(carryover_weight, 4)
    screen_semantic_weight = round(clamp(0.16 + 0.22 * maturity + 0.08 * (effective_consistency - 0.5)), 4)
    front_trust = round(clamp(screen_weight / max(screen_weight + posthoc_weight, 1e-6)), 4)
    return {
        "stage": stage,
        "maturity": round(maturity, 4),
        "observed_turns": observed_turns,
        "posthoc_samples": posthoc_samples,
        "consistency_samples": consistency_samples,
        "stable_prediction_hits": stable_prediction_hits,
        "prediction_agreement": round(prediction_agreement, 4),
        "consistency_rate": round(consistency_rate, 4),
        "agreement_confidence": round(agreement_confidence, 4),
        "effective_consistency": round(effective_consistency, 4),
        "consistency_shift": round(consistency_shift, 4),
        "weight_model": "independent_signal_weights",
        "screen_weight": screen_weight,
        "screen_semantic_weight": screen_semantic_weight,
        "prior_weight": prior_weight,
        "posthoc_weight": posthoc_weight,
        "carryover_weight": carryover_weight,
        "front_trust": front_trust,
        "posthoc_trust": round(clamp(1.0 - front_trust), 4),
    }


def _urgent_primary_signal(emotion_vector: dict[str, float], features: dict[str, Any]) -> bool:
    return (
        emotion_vector["urgency"] >= 0.62
        or features["blocking_ratio"] >= 0.25
        or features["missed_expectation_ratio"] >= 0.34
        or (features["typing_chaos"] >= 0.42 and (features["delay_pressure"] >= 0.4 or features["urgency_hits"] >= 1))
        or (features["textism_pressure"] >= 0.34 and (features["delay_pressure"] >= 0.34 or features["urgency_hits"] >= 1))
        or (features["delay_pressure"] >= 0.5 and (features["command_ratio"] >= 0.34 or features["directness_delta"] >= 0.34))
        or (features["delay_pressure"] >= 0.8 and (features["stall_ratio"] >= 0.25 or features["stuck_pressure"] >= 0.8))
        or (features["stuck_pressure"] >= 0.9 and (features["delay_pressure"] >= 0.45 or features["same_issue_mentions"] >= 1 or features["stall_ratio"] >= 0.25))
        or (features["stuck_pressure"] >= 0.78 and features["delay_pressure"] >= 0.55 and (features["frustration_ratio"] >= 0.25 or features["stall_ratio"] >= 0.25))
        or (features["stall_ratio"] >= 0.25 and features["delay_pressure"] >= 0.45 and emotion_vector["urgency"] >= 0.34)
        or (features["short_burst"] >= 0.75 and features["urgency_hits"] >= 1 and features["frustration_hits"] >= 1)
        or (features["missed_expectation_ratio"] >= 0.28 and features["delay_pressure"] >= 0.45 and (features["same_issue_mentions"] >= 1 or features["frustration_ratio"] >= 0.75))
        or (features["explicit_confusion_request"] >= 1.0 and features["evidence_request"] >= 1.0 and features["goal_specificity"] <= 0.18 and features["unresolved_turns"] >= 2)
    )


def _urgent_secondary_signal(features: dict[str, Any]) -> bool:
    return (
        (features["urgency_hits"] >= 1 and (features["goal_specificity"] >= 0.25 or features["guardrail_request"] >= 1.0 or features["command_ratio"] >= 0.25))
        or (features["delay_pressure"] >= 0.6 and (features["frustration_ratio"] >= 0.25 or features["stuck_pressure"] >= 0.55 or features["same_issue_mentions"] >= 1))
        or (features["frustration_ratio"] >= 0.75 and features["same_issue_mentions"] >= 1 and features["delay_pressure"] >= 0.4)
        or (features["frustration_ratio"] >= 0.5 and features["same_issue_mentions"] >= 1 and features["delay_pressure"] >= 0.35 and features["stuck_pressure"] >= 0.7)
        or features["blocking_ratio"] >= 0.25
    )


def _frustrated_primary_signal(emotion_vector: dict[str, float], features: dict[str, Any]) -> bool:
    return (
        emotion_vector["frustration"] >= 0.6
        or features["frustration_ratio"] >= 0.32
        or features["missed_expectation_ratio"] >= 0.34
        or features["context_loss_ratio"] >= 0.34
        or features["execution_plumbing_ratio"] >= 0.34
        or features["resolution_mismatch"] >= 0.5
        or features["stall_ratio"] >= 0.5
        or (features["stall_ratio"] >= 0.25 and features["delay_pressure"] >= 0.42 and (features["urgency_hits"] >= 1 or features["missed_expectation_ratio"] >= 0.25 or features["same_issue_mentions"] >= 1))
        or (features["abrupt_delta"] >= 0.35 and features["delay_pressure"] >= 0.45)
        or (features["dismissive_pressure"] >= 0.38 and (features["delay_pressure"] >= 0.28 or features["stuck_pressure"] >= 0.42 or features["resolution_mismatch"] >= 0.5))
        or (features["stuck_pressure"] >= 0.8 and (features["frustration_ratio"] >= 0.25 or features["stall_ratio"] >= 0.25 or features["delay_pressure"] >= 0.35))
        or ((features["contradiction_signal"] >= 0.4 or features["soft_correction"] >= 0.8) and features["same_issue_mentions"] >= 1 and (features["skepticism_ratio"] >= 0.25 or features["speculation_ratio"] >= 0.25 or features["context_loss_ratio"] >= 0.25))
        or (features["speculation_ratio"] >= 0.75 and (features["delay_pressure"] >= 0.28 or features["contradiction_signal"] >= 0.28 or features["stuck_pressure"] >= 0.28))
        or (features["skepticism_ratio"] >= 0.3 and features["stuck_pressure"] >= 0.52 and features["contradiction_signal"] >= 0.28)
    )


def _frustrated_secondary_signal(features: dict[str, Any]) -> bool:
    return (
        features["blocking_ratio"] >= 0.25
        or (features["execution_plumbing_ratio"] >= 0.25 and (features["task_object_ratio"] >= 0.25 or features["same_issue_mentions"] >= 1))
        or (features["frustration_ratio"] >= 0.25 and (features["stuck_pressure"] >= 0.45 or features["delay_pressure"] >= 0.42))
        or (features["missed_expectation_ratio"] >= 0.25 and (features["evidence_request"] >= 1.0 or features["technical_ratio"] >= 0.15))
    )


def _confused_primary_signal(emotion_vector: dict[str, float], features: dict[str, Any]) -> bool:
    explicit_or_low_clarity = (
        emotion_vector["confusion"] >= 0.58
        and (
            features["explicit_confusion_request"] >= 1.0
            or features["questions"] >= 1
            or (features["vague_ratio"] >= 0.3 and features["hedge_ratio"] >= 0.3 and features["goal_specificity"] <= 0.18)
            or (features["goal_specificity"] <= 0.22 and features["evidence_request"] == 0.0 and features["comparison_request"] == 0.0 and features["guardrail_request"] == 0.0)
        )
    )
    explicit_goal_mismatch = features["explicit_confusion_request"] >= 1.0 and features["goal_specificity"] <= 0.68
    vague_low_pressure = (
        features["vague_ratio"] >= 0.3
        and features["hedge_ratio"] >= 0.3
        and features["goal_specificity"] <= 0.18
        and emotion_vector["urgency"] <= 0.45
        and emotion_vector["frustration"] <= 0.42
    )
    return (explicit_or_low_clarity or explicit_goal_mismatch or vague_low_pressure) and emotion_vector["urgency"] <= 0.78 and emotion_vector["frustration"] <= 0.76


def _confused_context_loss_signal(emotion_vector: dict[str, float], features: dict[str, Any]) -> bool:
    return features["confusion_hits"] >= 2 and features["context_loss_ratio"] >= 0.25 and emotion_vector["urgency"] <= 0.42


def _confused_execution_signal(emotion_vector: dict[str, float], features: dict[str, Any]) -> bool:
    return features["confusion_hits"] >= 2 and features["execution_plumbing_ratio"] >= 0.34 and features["goal_specificity"] <= 0.18 and emotion_vector["urgency"] <= 0.45


def _confused_evidence_gap_signal(features: dict[str, Any]) -> bool:
    return features["confusion_hits"] >= 1 and features["evidence_request"] >= 1.0 and features["contradiction_signal"] >= 0.18 and features["goal_specificity"] <= 0.24


def _confused_evidence_skepticism_signal(features: dict[str, Any]) -> bool:
    return features["confusion_hits"] >= 1 and features["evidence_request"] >= 1.0 and features["skepticism_ratio"] >= 0.25 and features["contradiction_signal"] >= 0.18


def _skeptical_primary_signal(emotion_vector: dict[str, float], features: dict[str, Any]) -> bool:
    return (
        emotion_vector["skepticism"] >= 0.42
        or features["skepticism_ratio"] >= 0.32
        or features["speculation_ratio"] >= 0.25
        or features["context_loss_ratio"] >= 0.25
        or features["execution_plumbing_ratio"] >= 0.25
        or (features["hedge_ratio"] >= 0.34 and (features["contradiction_signal"] >= 0.25 or features["speculation_ratio"] >= 0.25 or features["evidence_request"] >= 1.0))
        or features["resolution_mismatch"] >= 0.5
        or features["contradiction_signal"] >= 0.45
        or features["evidence_request"] >= 1.0
        or (features["dismissive_pressure"] >= 0.42 and (features["hedge_ratio"] >= 0.2 or features["contradiction_signal"] >= 0.25 or features["goal_specificity"] >= 0.28))
        or (features["missed_expectation_ratio"] >= 0.25 and features["contradiction_signal"] >= 0.24 and features["delay_pressure"] >= 0.5)
    )


def _skeptical_secondary_signal(features: dict[str, Any]) -> bool:
    return (
        features["skepticism_ratio"] >= 0.25
        or (features["questions"] >= 1 and features["stuck_pressure"] >= 0.5)
        or (features["evidence_request"] >= 1.0 and features["task_object_ratio"] >= 0.3)
    )


def _satisfied_signal(emotion_vector: dict[str, float], features: dict[str, Any]) -> bool:
    return (
        emotion_vector["satisfaction"] >= 0.6
        or (features["guard_ratio"] >= 0.3 and (features["success_ratio"] >= 0.3 or features["satisfaction_hits"] >= 1 or features["resolution_claimed"] >= 0.5))
        or ((features["satisfaction_hits"] >= 1 or features["resolution_claimed"] >= 0.5 or features["success_hits"] >= 1) and features["continue_ratio"] >= 0.25)
    )


def _cautious_signal(emotion_vector: dict[str, float], features: dict[str, Any]) -> bool:
    return (
        emotion_vector["cautiousness"] >= 0.42
        or features["caution_ratio"] >= 0.3
        or features["boundary_ratio"] >= 0.3
        or features["assurance_ratio"] >= 0.3
        or features["guardrail_request"] >= 1.0
        or (features["context_loss_ratio"] >= 0.25 and features["speculation_ratio"] >= 0.25)
        or (features["context_loss_ratio"] >= 0.25 and features["evidence_request"] >= 1.0 and features["contradiction_signal"] >= 0.25)
    )


def _exploratory_primary_signal(emotion_vector: dict[str, float], features: dict[str, Any]) -> bool:
    return (emotion_vector["openness"] >= 0.4 or features["comparison_request"] >= 1.0) and emotion_vector["urgency"] <= 0.72 and emotion_vector["frustration"] <= 0.72


def _exploratory_secondary_signal(emotion_vector: dict[str, float], features: dict[str, Any]) -> bool:
    return features["explore_ratio"] >= 0.3 and (features["comparison_request"] >= 1.0 or features["evidence_request"] >= 1.0 or features["guardrail_request"] >= 1.0) and emotion_vector["frustration"] <= 0.72


def infer_labels(emotion_vector: dict[str, float], features: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    if _urgent_primary_signal(emotion_vector, features):
        labels.append("urgent")
    if _frustrated_primary_signal(emotion_vector, features):
        labels.append("frustrated")
    if "urgent" not in labels and _urgent_secondary_signal(features):
        labels.append("urgent")
    if "frustrated" not in labels and _frustrated_secondary_signal(features):
        labels.append("frustrated")
    if _confused_primary_signal(emotion_vector, features):
        labels.append("confused")
    if "confused" not in labels and _confused_context_loss_signal(emotion_vector, features):
        labels.append("confused")
    if "confused" not in labels and _confused_execution_signal(emotion_vector, features):
        labels.append("confused")
    if "confused" not in labels and _confused_evidence_gap_signal(features):
        labels.append("confused")
    if "confused" not in labels and _confused_evidence_skepticism_signal(features):
        labels.append("confused")
    if _skeptical_primary_signal(emotion_vector, features):
        labels.append("skeptical")
    if "skeptical" not in labels and _skeptical_secondary_signal(features):
        labels.append("skeptical")
    if _satisfied_signal(emotion_vector, features):
        labels.append("satisfied")
    if _cautious_signal(emotion_vector, features):
        labels.append("cautious")
    if _exploratory_primary_signal(emotion_vector, features):
        labels.append("exploratory")
    if "exploratory" not in labels and _exploratory_secondary_signal(emotion_vector, features):
        labels.append("exploratory")
    if not labels:
        labels.append("neutral")
    return canonicalize_labels(labels)


def initial_screen(features: FeatureMap) -> ScreenState:
    urgency = clamp(
        0.23 * clamp(features["urgency_hits"] / 2.0)
        + 0.12 * features["blocking_ratio"]
        + 0.12 * features["missed_expectation_ratio"]
        + 0.04 * features["execution_plumbing_ratio"]
        + 0.1 * features["command_ratio"]
        + 0.08 * features["directness_delta"]
        + 0.06 * features["short_burst"]
        + 0.06 * features["terseness_delta"]
        + 0.08 * features["typing_chaos"]
        + 0.1 * features["repeat_similarity"]
        + 0.18 * features["delay_pressure"]
        + 0.16 * features["stuck_pressure"]
        + 0.06 * features["punctuation_pressure"]
        + 0.04 * features["punctuation_delta"]
        + 0.05 * features["textism_pressure"]
        + 0.04 * features["tempo_pause_pressure"]
        + 0.1 * features["stall_ratio"]
        + 0.06 * features["goal_specificity"]
    )
    frustration = clamp(
        0.22 * clamp(features["anger_hits"] / 2.0)
        + 0.26 * features["frustration_ratio"]
        + 0.12 * features["missed_expectation_ratio"]
        + 0.08 * features["context_loss_ratio"]
        + 0.1 * features["execution_plumbing_ratio"]
        + 0.14 * features["stall_ratio"]
        + 0.1 * features["repeat_similarity"]
        + 0.14 * features["delay_pressure"]
        + 0.18 * features["stuck_pressure"]
        + 0.04 * features["punctuation_pressure"]
        + 0.06 * features["punctuation_delta"]
        + 0.16 * features["abrupt_delta"]
        + 0.08 * features["dismissive_pressure"]
        + 0.05 * features["tempo_pause_pressure"]
        + 0.03 * features["textism_pressure"]
        + 0.1 * features["resolution_mismatch"]
        + 0.04 * features["contradiction_signal"]
        + 0.04 * features["soft_correction"]
    )
    clarity = clamp(
        0.56
        + 0.12 * features["goal_specificity"]
        + 0.08 * features["task_object_ratio"]
        + 0.08 * features["technical_ratio"]
        + 0.06 * clamp(features["file_refs"] / 2.0)
        + 0.06 * clamp(features["code_markers"])
        + 0.05 * clamp(features["list_markers"] / 4.0)
        + 0.04 * features["boundary_ratio"]
        + 0.03 * features["guard_ratio"]
        + 0.05 * features["evidence_request"]
        + 0.05 * features["comparison_request"]
        + 0.05 * features["guardrail_request"]
        - (0.02 if features["explicit_confusion_request"] == 0 else 0.08) * features["question_density"]
        - 0.12 * features["vague_ratio"]
        - 0.04 * clamp(features["confusion_hits"] / 2.0)
        - 0.08 * features["explicit_confusion_request"]
        - 0.04 * (1.0 if features["chars"] <= 10 and features["goal_specificity"] < 0.3 else 0.0)
    )
    satisfaction = clamp(
        0.06
        + 0.24 * features["praise_ratio"]
        + 0.22 * features["success_ratio"]
        + 0.14 * features["continue_ratio"] * (1.0 if features["satisfaction_hits"] >= 1 or features["resolution_claimed"] >= 0.5 else 0.35)
        + 0.18 * features["guard_ratio"]
        + 0.08 * features["resolution_claimed"]
        + 0.04 * features["polite_ratio"]
        + 0.06 * features["politeness_delta"]
        - 0.28 * frustration
    )
    trust = clamp(
        0.4
        + 0.08 * features["polite_ratio"]
        + 0.08 * features["politeness_delta"]
        + 0.08 * features["caution_ratio"]
        + 0.06 * features["boundary_ratio"]
        + 0.1 * satisfaction
        - 0.14 * clamp(features["anger_hits"] / 2.0)
        - 0.14 * features["frustration_ratio"]
        - 0.14 * features["speculation_ratio"]
        - 0.08 * features["context_loss_ratio"]
        - 0.1 * features["execution_plumbing_ratio"]
        - 0.08 * features["dismissive_pressure"]
        - 0.08 * features["resolution_mismatch"]
        - 0.1 * features["contradiction_signal"]
    )
    engagement = clamp(
        0.28
        + 0.08 * clamp(features["chars"] / 220.0)
        + 0.08 * features["question_density"]
        + 0.12 * features["technical_ratio"]
        + 0.12 * clamp(features["same_issue_mentions"] / 3.0)
        + 0.08 * clamp(features["list_markers"] / 4.0)
        + 0.12 * features["stuck_pressure"]
        + 0.08 * clamp((features["punctuation_runs"] + features["latin_elongations"] + features["cjk_elongations"]) / 3.0)
    )

    vector = {
        "urgency": round(urgency, 4),
        "frustration": round(frustration, 4),
        "clarity": round(clarity, 4),
        "satisfaction": round(satisfaction, 4),
        "trust": round(trust, 4),
        "engagement": round(engagement, 4),
    }
    emotion_vector = derive_emotion_vector(vector, features)
    mode_scores = build_mode_scores(emotion_vector, features)
    confidence = clamp(
        0.54
        + 0.08 * clamp(len(features["evidence"]) / 5.0)
        + 0.08 * abs(vector["urgency"] - 0.5)
        + 0.08 * abs(vector["frustration"] - 0.5)
        + 0.06 * features["goal_specificity"]
        + 0.04 * features["surface_signal_reliability"]
        - 0.12 * features["surface_uncertainty"]
    )
    return {
        "vector": vector,
        "state_vector": vector,
        "interaction_state": build_interaction_state(vector),
        "emotion_vector": emotion_vector,
        "emotion_intensity": build_intensity_profile(emotion_vector),
        "mode_scores": mode_scores,
        "labels": infer_labels(emotion_vector, features),
        "confidence": round(confidence, 4),
        "evidence": features["evidence"],
    }


def blend_named_vector(base: dict[str, float], incoming: dict[str, Any], dims: tuple[str, ...], weight: float) -> dict[str, float]:
    if not incoming:
        return base
    result = dict(base)
    for dim in dims:
        incoming_value = incoming.get(dim)
        if incoming_value is None:
            continue
        result[dim] = round(clamp((1.0 - weight) * result[dim] + weight * float(incoming_value)), 4)
    return result


def blend_vectors(base: dict[str, float], incoming: dict[str, Any], weight: float) -> dict[str, float]:
    return blend_named_vector(base, incoming, DIMS, weight)


def derive_state_vector_from_emotion(emotion_vector: dict[str, Any], features: dict[str, Any]) -> dict[str, float]:
    emotion = clamp_dict(emotion_vector, EMOTION_DIMS)
    return {
        "urgency": round(emotion["urgency"], 4),
        "frustration": round(emotion["frustration"], 4),
        "clarity": round(clamp(0.64 - 0.46 * emotion["confusion"] - 0.12 * emotion["urgency"] - 0.08 * emotion["frustration"] + 0.08 * emotion["openness"] + 0.06 * features["task_object_ratio"] + 0.04 * features["goal_specificity"]), 4),
        "satisfaction": round(emotion["satisfaction"], 4),
        "trust": round(clamp(0.56 - 0.34 * emotion["skepticism"] - 0.22 * emotion["frustration"] + 0.1 * emotion["cautiousness"] + 0.08 * emotion["satisfaction"] + 0.04 * features["assurance_ratio"]), 4),
        "engagement": round(clamp(0.3 + 0.24 * emotion["urgency"] + 0.22 * emotion["frustration"] + 0.18 * emotion["openness"] + 0.08 * features["technical_ratio"]), 4),
    }


def dominant_mode(emotion_vector: dict[str, float], features: dict[str, Any], scores: dict[str, float] | None = None) -> str:
    scores = scores or build_mode_scores(emotion_vector, features)
    ev = emotion_vector
    f = features
    skeptical_gap = scores["confused"] - scores["skeptical"]

    rules = [
        DominantModeRule(
            "satisfied_from_success_guard",
            "satisfied",
            lambda: (
                (scores["satisfied"] >= 0.24 and f["guard_ratio"] >= 0.3 and (f["satisfaction_hits"] >= 1 or f["success_hits"] >= 1 or f["resolution_claimed"] >= 0.5))
                or (scores["satisfied"] >= 0.28 and f["continue_ratio"] >= 0.25 and (f["satisfaction_hits"] >= 1 or f["resolution_claimed"] >= 0.5 or f["success_hits"] >= 1))
                or (scores["satisfied"] >= 0.62 and ev["frustration"] <= 0.42)
            ),
        ),
        DominantModeRule(
            "cautious_from_safety_language",
            "cautious",
            lambda: (
                scores["cautious"] >= 0.34
                and (f["caution_ratio"] >= 0.25 or f["boundary_ratio"] >= 0.25 or f["assurance_ratio"] >= 0.25)
                and scores["urgent"] - scores["cautious"] <= 0.18
                and (f["evidence_request"] == 0.0 or scores["skeptical"] <= scores["cautious"] + 0.06)
                and not (f["evidence_request"] >= 1.0 and (f["same_issue_mentions"] >= 1 or f["frustration_hits"] >= 1 or f["stall_ratio"] >= 0.25))
            ),
        ),
        DominantModeRule(
            "confused_from_evidence_and_low_specificity",
            "confused",
            lambda: scores["confused"] >= 0.18 and f["explicit_confusion_request"] >= 1.0 and f["evidence_request"] >= 1.0 and f["goal_specificity"] <= 0.18 and f["unresolved_turns"] >= 2 and scores["urgent"] <= 0.32,
        ),
        DominantModeRule(
            "exploratory_from_clean_comparison",
            "exploratory",
            lambda: f["comparison_request"] >= 1.0 and scores["exploratory"] >= 0.3 and f["frustration_ratio"] == 0.0 and scores["exploratory"] >= scores["skeptical"] - 0.14,
        ),
        DominantModeRule(
            "frustrated_from_stuck_delay",
            "frustrated",
            lambda: scores["frustrated"] >= 0.42 and f["stuck_pressure"] >= 0.8 and f["delay_pressure"] >= 0.5 and f["frustration_ratio"] >= 0.25 and f["urgency_hits"] == 0 and f["blocking_ratio"] < 0.25 and f["comparison_request"] == 0.0,
        ),
        DominantModeRule(
            "skeptical_from_evidence_request",
            "skeptical",
            lambda: scores["skeptical"] >= 0.34 and f["evidence_request"] >= 1.0 and scores["urgent"] - scores["skeptical"] <= 0.14,
        ),
        DominantModeRule(
            "skeptical_from_trust_gap",
            "skeptical",
            lambda: scores["skeptical"] >= 0.34 and f["skepticism_ratio"] >= 0.25 and (f["evidence_request"] >= 1.0 or f["contradiction_signal"] >= 0.3 or f["stuck_pressure"] >= 0.6) and scores["frustrated"] - scores["skeptical"] <= 0.1,
        ),
        DominantModeRule(
            "exploratory_from_comparison_low_pressure",
            "exploratory",
            lambda: scores["exploratory"] >= 0.3 and f["comparison_request"] >= 1.0 and ev["urgency"] <= 0.72 and ev["frustration"] <= 0.72 and scores["exploratory"] >= scores["confused"] - 0.06 and scores["exploratory"] >= max(scores["frustrated"], scores["skeptical"]) - 0.02 and f["stuck_pressure"] <= 0.52,
        ),
        DominantModeRule(
            "cautious_from_guardrail_request",
            "cautious",
            lambda: scores["cautious"] >= 0.28 and f["guardrail_request"] >= 1.0 and scores["urgent"] - scores["cautious"] <= 0.14,
        ),
        DominantModeRule(
            "urgent_from_direct_pressure",
            "urgent",
            lambda: scores["urgent"] >= 0.5 and (f["urgency_hits"] >= 1 or f["rush_typo_hits"] >= 1 or f["textism_hits"] >= 1),
        ),
        DominantModeRule(
            "urgent_from_blocked_request",
            "urgent",
            lambda: f["urgency_hits"] >= 1 and f["blocking_ratio"] >= 0.25 and scores["urgent"] >= scores["frustrated"] - 0.12,
        ),
        DominantModeRule(
            "confused_from_low_specificity",
            "confused",
            lambda: scores["confused"] >= 0.24 and f["explicit_confusion_request"] >= 1.0 and f["goal_specificity"] <= 0.18 and f["evidence_request"] == 0.0 and f["comparison_request"] == 0.0 and f["guardrail_request"] == 0.0 and scores["confused"] >= scores["skeptical"] - 0.04,
        ),
        DominantModeRule(
            "confused_from_question_signal",
            "confused",
            lambda: scores["confused"] >= 0.16 and ((f["explicit_confusion_request"] >= 1.0 and f["questions"] >= 1) or (f["confusion_hits"] >= 1 and f["questions"] >= 1 and scores["urgent"] - scores["confused"] <= 0.24)),
        ),
        DominantModeRule(
            "confused_from_vague_low_pressure",
            "confused",
            lambda: f["vague_ratio"] >= 0.3 and f["hedge_ratio"] >= 0.3 and f["goal_specificity"] <= 0.18 and ev["urgency"] <= 0.45 and ev["frustration"] <= 0.42,
        ),
        DominantModeRule(
            "frustrated_from_abrupt_delay",
            "frustrated",
            lambda: f["abrupt_delta"] >= 0.35 and f["delay_pressure"] >= 0.45,
        ),
        DominantModeRule(
            "frustrated_from_dismissive_stuck",
            "frustrated",
            lambda: f["dismissive_pressure"] >= 0.34 and (f["stuck_pressure"] >= 0.6 or f["delay_pressure"] >= 0.5),
        ),
        DominantModeRule(
            "frustrated_from_stall",
            "frustrated",
            lambda: f["stall_ratio"] >= 0.6 and f["stuck_pressure"] >= 0.8 and f["blocking_ratio"] < 0.25 and scores["frustrated"] >= scores["urgent"] - 0.05,
        ),
        DominantModeRule(
            "urgent_from_delayed_blocking",
            "urgent",
            lambda: scores["urgent"] >= 0.5 and f["blocking_ratio"] >= 0.25 and f["delay_pressure"] >= 0.85 and scores["urgent"] >= scores["frustrated"] - 0.04,
        ),
        DominantModeRule(
            "frustrated_from_general_stuck",
            "frustrated",
            lambda: scores["frustrated"] >= 0.42 and scores["frustrated"] >= scores["urgent"] - 0.08 and (f["stuck_pressure"] >= 0.72 or f["delay_pressure"] >= 0.45 or f["frustration_ratio"] >= 0.25 or f["blocking_ratio"] >= 0.25),
        ),
        DominantModeRule(
            "urgent_from_high_score_gap",
            "urgent",
            lambda: scores["urgent"] >= 0.72 and (f["blocking_ratio"] >= 0.25 or scores["urgent"] - max(scores["frustrated"], scores["skeptical"], scores["cautious"]) >= 0.08),
        ),
        DominantModeRule(
            "frustrated_from_high_score",
            "frustrated",
            lambda: scores["frustrated"] >= 0.64 and scores["frustrated"] >= scores["confused"] - 0.02,
        ),
        DominantModeRule(
            "urgent_from_delay_and_stall",
            "urgent",
            lambda: f["delay_pressure"] >= 0.8 and (f["stall_ratio"] >= 0.25 or f["stuck_pressure"] >= 0.8) and scores["urgent"] >= scores["frustrated"] + 0.08,
        ),
        DominantModeRule(
            "urgent_from_dominant_score",
            "urgent",
            lambda: scores["urgent"] >= 0.64 and scores["urgent"] >= max(scores["confused"], scores["frustrated"] + 0.08, scores["skeptical"] + 0.1, scores["cautious"] + 0.12),
        ),
        DominantModeRule(
            "skeptical_from_mixed_evidence_gap",
            "skeptical",
            lambda: scores["skeptical"] >= 0.38
            and (
                (f["evidence_request"] >= 1.0 and skeptical_gap <= 0.2)
                or (f["speculation_ratio"] >= 0.25 and skeptical_gap <= 0.16)
                or (f["context_loss_ratio"] >= 0.25 and skeptical_gap <= 0.16)
                or (f["execution_plumbing_ratio"] >= 0.25 and skeptical_gap <= 0.16)
                or (f["skepticism_ratio"] >= 0.25 and skeptical_gap <= 0.12)
                or (f["contradiction_signal"] >= 0.3 and skeptical_gap <= 0.12)
                or f["resolution_mismatch"] >= 0.4
            ),
        ),
        DominantModeRule(
            "skeptical_from_broad_signal",
            "skeptical",
            lambda: scores["skeptical"] >= 0.36 and (ev["skepticism"] >= 0.34 or f["skepticism_ratio"] >= 0.25 or f["context_loss_ratio"] >= 0.25 or f["execution_plumbing_ratio"] >= 0.25 or f["resolution_mismatch"] >= 0.4 or f["contradiction_signal"] >= 0.4),
        ),
        DominantModeRule(
            "cautious_from_broad_signal",
            "cautious",
            lambda: scores["cautious"] >= 0.34 and (ev["cautiousness"] >= 0.3 or f["caution_ratio"] >= 0.25 or f["boundary_ratio"] >= 0.25 or f["assurance_ratio"] >= 0.25),
        ),
        DominantModeRule(
            "exploratory_from_high_score",
            "exploratory",
            lambda: scores["exploratory"] >= 0.54,
        ),
        DominantModeRule(
            "confused_from_high_score",
            "confused",
            lambda: scores["confused"] >= 0.56,
        ),
    ]

    for rule in rules:
        if rule.predicate():
            return rule.mode

    best_non_neutral = max((name for name in scores if name != "neutral"), key=scores.get)
    if scores[best_non_neutral] >= 0.18 and (
        f["frustration_hits"] >= 1
        or f["stall_ratio"] >= 0.25
        or f["skepticism_hits"] >= 1
        or f["speculation_ratio"] >= 0.25
        or f["context_loss_ratio"] >= 0.25
        or f["execution_plumbing_ratio"] >= 0.25
        or f["evidence_request"] >= 1.0
        or f["guardrail_request"] >= 1.0
        or f["comparison_request"] >= 1.0
    ):
        return best_non_neutral
    return "neutral"


def confirm_state(payload: dict[str, Any], features: FeatureMap, screen: ScreenState, weight_schedule: dict[str, Any]) -> ConfirmedState:
    llm_semantic = payload.get("llm_semantic") or {}
    llm_confidence = clamp(float(llm_semantic.get("confidence", 0.0) or 0.0))
    llm_state_vector = clamp_dict(llm_semantic.get("vector"), STATE_DIMS) if llm_semantic.get("vector") else {}
    if not llm_state_vector and llm_semantic.get("emotion_vector"):
        llm_state_vector = derive_state_vector_from_emotion(llm_semantic["emotion_vector"], features)
    last_state = payload.get("last_state") or {}
    previous_vector = last_state.get("vector") or {}
    ttl_seconds = int(last_state.get("ttl_seconds", 0) or 0)
    prev_weight = weight_schedule["carryover_weight"] if ttl_seconds > 0 else 0.0
    vector_inputs: list[tuple[dict[str, Any], float]] = [(screen["vector"], weight_schedule["screen_weight"])]
    if llm_state_vector:
        vector_inputs.append((llm_state_vector, weight_schedule["screen_semantic_weight"] * llm_confidence))
    if previous_vector:
        vector_inputs.append((previous_vector, prev_weight))
    vector = combine_named_vectors(vector_inputs, STATE_DIMS)
    emotion_vector = derive_emotion_vector(vector, features)
    profile_prior = features["user_profile"].get("affective_prior") or {}
    profile_prior_weight = clamp(float(features["user_profile"].get("affective_prior_weight", 0.0) or 0.0), 0.0, 0.24)
    review_semantic = load_review_semantic(payload)
    posthoc_confidence = clamp(float(review_semantic.get("confidence", 0.0) or 0.0))
    previous_emotion_vector = last_state.get("emotion_vector") or {}
    emotion_inputs: list[tuple[dict[str, Any], float]] = [(emotion_vector, weight_schedule["screen_weight"])]
    if profile_prior:
        emotion_inputs.append((profile_prior, min(profile_prior_weight, weight_schedule["prior_weight"])))
    if llm_semantic.get("emotion_vector"):
        emotion_inputs.append((llm_semantic["emotion_vector"], weight_schedule["screen_semantic_weight"] * llm_confidence))
    if review_semantic.get("emotion_vector"):
        emotion_inputs.append((review_semantic["emotion_vector"], weight_schedule["posthoc_weight"] * max(posthoc_confidence, 0.55)))
    if previous_emotion_vector:
        emotion_inputs.append((previous_emotion_vector, prev_weight))
    emotion_vector = combine_named_vectors(emotion_inputs, EMOTION_DIMS)
    labels = infer_labels(emotion_vector, features)
    if llm_semantic.get("labels"):
        for label in llm_semantic["labels"]:
            if label not in labels:
                labels.append(label)
    if review_semantic.get("labels"):
        for label in review_semantic["labels"]:
            if label not in labels:
                labels.append(label)
    mode_scores = build_mode_scores(emotion_vector, features)
    mode = dominant_mode(emotion_vector, features, mode_scores)
    if mode != "neutral" and mode not in labels:
        labels = [mode] if labels == ["neutral"] else labels + [mode]
    if mode in {"urgent", "frustrated"}:
        ttl = 1800
    elif mode == "cautious":
        ttl = 1500
    elif mode == "confused":
        ttl = 1200
    else:
        ttl = 900
    confidence = clamp(
        screen["confidence"] * 0.56
        + llm_confidence * 0.16
        + posthoc_confidence * 0.22
        + 0.03 * features["surface_signal_reliability"]
        - 0.05 * features["surface_uncertainty"]
        + 0.04 * abs(vector["urgency"] - vector["frustration"])
    )
    return {
        "dominant_mode": mode,
        "labels": canonicalize_labels(labels),
        "confidence": round(confidence, 4),
        "ttl_seconds": ttl,
        "vector": {dim: round(clamp(vector[dim]), 4) for dim in DIMS},
        "state_vector": {dim: round(clamp(vector[dim]), 4) for dim in DIMS},
        "interaction_state": build_interaction_state(vector),
        "emotion_vector": {dim: round(clamp(emotion_vector[dim]), 4) for dim in EMOTION_DIMS},
        "emotion_intensity": build_intensity_profile(emotion_vector),
        "emotionality_metrics": build_emotionality_metrics(emotion_vector, features),
        "mode_scores": mode_scores,
        "weight_schedule": weight_schedule,
        "evidence": screen["evidence"],
    }


def build_consistency_snapshot(payload: dict[str, Any], screen: dict[str, Any]) -> dict[str, Any]:
    review_semantic = load_review_semantic(payload)
    if not review_semantic:
        return {
            "available": False,
            "consistency_rate": 0.0,
            "label_overlap": 0.0,
            "vector_alignment": 0.0,
            "axis_overlap": 0.0,
            "screen_labels": canonicalize_labels(screen.get("labels", [])),
            "posthoc_labels": [],
        }
    screen_vector = clamp_dict(screen.get("emotion_vector"), EMOTION_DIMS)
    posthoc_vector = clamp_dict(review_semantic.get("emotion_vector"), EMOTION_DIMS)
    screen_labels = canonicalize_labels(screen.get("labels", []))
    posthoc_labels = canonicalize_labels(list(review_semantic.get("labels") or []))
    label_overlap = label_overlap_score(screen_labels, posthoc_labels)
    vector_alignment = vector_alignment_score(screen_vector, posthoc_vector, EMOTION_DIMS)
    axis_overlap = axis_overlap_score(screen_vector, posthoc_vector, EMOTION_DIMS)
    consistency_rate = round(clamp(0.44 * label_overlap + 0.36 * vector_alignment + 0.2 * axis_overlap), 4)
    return {
        "available": True,
        "consistency_rate": consistency_rate,
        "label_overlap": label_overlap,
        "vector_alignment": vector_alignment,
        "axis_overlap": axis_overlap,
        "screen_labels": screen_labels,
        "posthoc_labels": posthoc_labels,
    }
