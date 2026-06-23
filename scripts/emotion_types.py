from __future__ import annotations

from typing import Any, TypedDict


class FeatureMap(TypedDict, total=False):
    message: str
    language: str
    user_profile: dict[str, Any]
    evidence: list[str]


class ScreenState(TypedDict, total=False):
    vector: dict[str, float]
    state_vector: dict[str, float]
    interaction_state: dict[str, float]
    emotion_vector: dict[str, float]
    labels: list[str]
    confidence: float
    evidence: list[str]


class ConfirmedState(TypedDict, total=False):
    dominant_mode: str
    labels: list[str]
    confidence: float
    vector: dict[str, float]
    state_vector: dict[str, float]
    interaction_state: dict[str, float]
    emotion_vector: dict[str, float]
    mode_scores: dict[str, float]


class RoutingState(TypedDict, total=False):
    reply_style: str
    verification_level: str
    thread_interface: dict[str, Any]


class PipelineResult(TypedDict, total=False):
    schema_version: str
    degraded: bool
    degradation_reasons: list[str]
    host_capabilities: dict[str, Any]
    cli_options: dict[str, Any]
    profile_state: dict[str, Any]
    memory_update: dict[str, Any]
    constraint_signals: dict[str, Any]
    weight_schedule: dict[str, Any]
    collection_stack: dict[str, Any]
    consistency_snapshot: dict[str, Any]
    review_plan: dict[str, Any]
    posthoc_plan: dict[str, Any]
    review_shadow: dict[str, Any]
    posthoc_shadow: dict[str, Any]
    features: FeatureMap
    initial_screen: ScreenState
    confirmed_state: ConfirmedState
    prediction: dict[str, Any]
    analysis: dict[str, Any]
    routing: RoutingState
    route_reasons: list[str]
    response_constraints: list[str]
    state_delta: dict[str, Any]
    satisfaction_lock: dict[str, Any]
    guidance: dict[str, Any]
    overlay_prompt: str
    debug_overlay_prompt: str
    prompts: dict[str, str]
    pipeline_profile: dict[str, Any]


STATE_DIMS = ("urgency", "frustration", "clarity", "satisfaction", "trust", "engagement")
INTERACTION_DIMS = ("clarity", "trust", "engagement")
EMOTION_DIMS = ("urgency", "frustration", "confusion", "skepticism", "satisfaction", "cautiousness", "openness")
DIMS = STATE_DIMS
DEFAULT_BASELINE = {
    "response_delay_seconds": 35.0,
    "politeness": 0.2,
    "terseness": 0.35,
    "punctuation": 0.15,
    "directness": 0.3,
}
DEFAULT_PERSONA_TRAITS = {
    "patience": 0.5,
    "skepticism": 0.35,
    "caution": 0.35,
    "openness": 0.5,
    "assertiveness": 0.4,
}
SCHEMA_VERSION = "1.3.1"
MAX_DEGRADATION_REASONS = 32
MAX_ROUTE_REASONS = 6
SUPPORTED_OUTPUT_LANGUAGES = {"en", "zh"}
LABEL_ORDER = ("urgent", "frustrated", "confused", "skeptical", "cautious", "exploratory", "satisfied", "neutral")
LABEL_ORDER_INDEX = {label: index for index, label in enumerate(LABEL_ORDER)}
STATE_SHIFT_ALIASES = {
    "rising_frustration": "needs_concrete_unblock",
    "rising_urgency": "needs_priority_action",
    "falling_trust": "needs_evidence_first",
    "falling_clarity": "needs_alignment_check",
    "rising_satisfaction": "ready_for_closeout",
    "satisfaction_drop": "needs_stabilization",
    "changed": "needs_recheck",
    "stable": "stable",
    "new_turn": "new_turn",
}
ROUTE_REASON_ENUM = {
    "runtime_priority",
    "urgent_pressure",
    "repeat_failure_pressure",
    "evidence_requested",
    "scope_guard_requested",
    "low_clarity",
    "post_success_guard",
    "stall_risk",
    "needs_concrete_unblock",
    "needs_priority_action",
    "needs_evidence_first",
    "needs_alignment_check",
    "needs_stabilization",
    "ready_for_closeout",
    "task_specific",
}
RAW_HOST_CAPABILITY_KEYS = ("include_raw_emotion", "include_internal_diagnostics")
CLI_RAW_EMOTION_REQUEST_KEY = "_cli_include_raw_emotion"
INTERACTION_NEED_ENUM = {
    "alignment_check",
    "evidence_first",
    "keep_progress_visible",
}
