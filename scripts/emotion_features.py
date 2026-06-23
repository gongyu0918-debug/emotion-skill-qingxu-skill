from __future__ import annotations

from datetime import datetime
from difflib import SequenceMatcher
from typing import Any
from zoneinfo import ZoneInfo

from emotion_terms import *
from emotion_types import *
from emotion_utils import *


def derive_persona_traits(user_profile: dict[str, Any], diagnostics: dict[str, Any] | None = None) -> tuple[dict[str, float], str]:
    persona_traits = clamp_dict(user_profile.get("persona_traits"), tuple(DEFAULT_PERSONA_TRAITS.keys()), DEFAULT_PERSONA_TRAITS, diagnostics, "user_profile.persona_traits")
    source = "default"
    big5 = clamp_dict(user_profile.get("big5"), ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"), diagnostics=diagnostics, reason_prefix="user_profile.big5")
    if any(value > 0 for value in big5.values()):
        source = "big5"
        persona_traits = {
            "patience": round(clamp(0.42 + 0.22 * big5["agreeableness"] - 0.18 * big5["neuroticism"]), 4),
            "skepticism": round(clamp(0.14 + 0.18 * big5["conscientiousness"] + 0.12 * (1.0 - big5["agreeableness"])), 4),
            "caution": round(clamp(0.16 + 0.34 * big5["conscientiousness"] + 0.08 * big5["neuroticism"]), 4),
            "openness": round(clamp(big5["openness"]), 4),
            "assertiveness": round(clamp(0.1 + 0.8 * big5["extraversion"]), 4),
        }
    explicit_raw = user_profile.get("persona_traits")
    explicit = clamp_dict(explicit_raw, tuple(DEFAULT_PERSONA_TRAITS.keys()), diagnostics=diagnostics, reason_prefix="user_profile.persona_traits")
    explicit_mapping = explicit_raw if isinstance(explicit_raw, dict) else {}
    if any(value > 0 for value in explicit.values()):
        source = "persona_traits"
        persona_traits = {
            key: round(explicit[key] if key in explicit_mapping else persona_traits[key], 4)
            for key in DEFAULT_PERSONA_TRAITS
        }
    return persona_traits, source


def derive_affective_prior(user_profile: dict[str, Any], persona_traits: dict[str, float], persona_source: str, diagnostics: dict[str, Any] | None = None) -> tuple[dict[str, float], str, float]:
    explicit_prior = clamp_dict(user_profile.get("affective_prior") or user_profile.get("background_emotion"), EMOTION_DIMS, diagnostics=diagnostics, reason_prefix="user_profile.affective_prior")
    if any(value > 0 for value in explicit_prior.values()):
        return explicit_prior, "explicit", 0.22
    patience = persona_traits["patience"]
    skepticism = persona_traits["skepticism"]
    caution = persona_traits["caution"]
    openness = persona_traits["openness"]
    assertiveness = persona_traits["assertiveness"]
    inferred = {
        "urgency": round(clamp(0.04 + 0.12 * (1.0 - patience) + 0.08 * assertiveness), 4),
        "frustration": round(clamp(0.03 + 0.14 * (1.0 - patience)), 4),
        "confusion": 0.04,
        "skepticism": round(clamp(0.04 + 0.26 * skepticism + 0.08 * caution), 4),
        "satisfaction": round(clamp(0.08 + 0.08 * patience), 4),
        "cautiousness": round(clamp(0.05 + 0.24 * caution), 4),
        "openness": round(clamp(0.06 + 0.24 * openness), 4),
    }
    weight = 0.1 if persona_source in {"persona_traits", "big5"} else 0.0
    return inferred, "persona_heuristic", weight


def recent_user_messages(history: list[dict[str, Any]], limit: int = 5) -> list[str]:
    messages = []
    for item in history or []:
        if str(item.get("role", "")).lower() == "user":
            text = item.get("text") or item.get("content") or ""
            if text:
                messages.append(str(text))
    return messages[-limit:]


def last_assistant_message(history: list[dict[str, Any]]) -> str:
    for item in reversed(history or []):
        if str(item.get("role", "")).lower() == "assistant":
            return str(item.get("text") or item.get("content") or "")
    return ""


def load_review_semantic(payload: dict[str, Any]) -> dict[str, Any]:
    review_semantic = payload.get("review_semantic")
    if isinstance(review_semantic, dict) and review_semantic:
        return review_semantic
    legacy_review = payload.get("posthoc_semantic")
    if isinstance(legacy_review, dict) and legacy_review:
        return legacy_review
    return {}


def max_similarity(text: str, candidates: list[str]) -> float:
    norm = normalize_text(text)
    if not norm or not candidates:
        return 0.0
    scores = [SequenceMatcher(None, norm, normalize_text(candidate)).ratio() for candidate in candidates if candidate]
    return max(scores, default=0.0)


def parse_hour_window(raw: Any) -> tuple[int, int]:
    try:
        if isinstance(raw, (list, tuple)) and len(raw) >= 2:
            start = int(raw[0])
            end = int(raw[1])
        else:
            start, end = 9, 22
    except (TypeError, ValueError):
        start, end = 9, 22
    return max(0, min(23, start)), max(0, min(23, end))


def hour_in_window(hour: int | None, start: int, end: int) -> bool | None:
    if hour is None:
        return None
    if start == end:
        return True
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


def infer_local_hour(payload: dict[str, Any], timezone_name: str | None, diagnostics: dict[str, Any]) -> int | None:
    context = payload.get("context") or {}
    runtime = payload.get("runtime") or {}
    explicit_hour = context.get("local_hour")
    if explicit_hour is None:
        explicit_hour = runtime.get("local_hour")
    if explicit_hour is not None:
        try:
            return max(0, min(23, int(explicit_hour)))
        except (TypeError, ValueError):
            mark_degraded(diagnostics, "local_hour_invalid")
            return None
    now_iso = context.get("now_iso") or runtime.get("now_iso")
    if not now_iso:
        return None
    try:
        dt = datetime.fromisoformat(str(now_iso).replace("Z", "+00:00"))
    except Exception:
        mark_degraded(diagnostics, "now_iso_invalid")
        return None
    if not timezone_name:
        return int(dt.hour)
    try:
        tz = ZoneInfo(timezone_name)
    except Exception:
        return int(dt.hour)
    try:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
        else:
            dt = dt.astimezone(tz)
        return int(dt.hour)
    except Exception:
        mark_degraded(diagnostics, "now_iso_invalid")
        return None


def load_user_profile(payload: dict[str, Any], diagnostics: dict[str, Any]) -> dict[str, Any]:
    user_profile = payload.get("user_profile") or {}
    baseline = as_mapping(user_profile.get("baseline"), diagnostics, "user_profile.baseline_not_mapping")
    persona_traits, persona_source = derive_persona_traits(user_profile, diagnostics)
    affective_prior, affective_prior_source, affective_prior_weight = derive_affective_prior(user_profile, persona_traits, persona_source, diagnostics)
    timezone_name = user_profile.get("timezone") or payload.get("context", {}).get("timezone")
    work_start, work_end = parse_hour_window(user_profile.get("work_hours_local") or user_profile.get("work_hours"))
    local_hour = infer_local_hour(payload, timezone_name, diagnostics)
    in_work_window = hour_in_window(local_hour, work_start, work_end)
    baseline_delay = max(12.0, safe_float(baseline.get("response_delay_seconds"), DEFAULT_BASELINE["response_delay_seconds"], diagnostics, "user_profile.baseline.response_delay_seconds_invalid"))
    baseline_politeness = clamp(safe_float(baseline.get("politeness"), DEFAULT_BASELINE["politeness"], diagnostics, "user_profile.baseline.politeness_invalid"))
    baseline_terseness = clamp(safe_float(baseline.get("terseness", baseline.get("terse")), DEFAULT_BASELINE["terseness"], diagnostics, "user_profile.baseline.terseness_invalid"))
    baseline_punctuation = clamp(safe_float(baseline.get("punctuation"), DEFAULT_BASELINE["punctuation"], diagnostics, "user_profile.baseline.punctuation_invalid"))
    baseline_directness = clamp(safe_float(baseline.get("directness"), DEFAULT_BASELINE["directness"], diagnostics, "user_profile.baseline.directness_invalid"))
    availability_multiplier = 1.35 if in_work_window is False else 1.0
    return {
        "id": user_profile.get("id", ""),
        "timezone": timezone_name or "",
        "local_hour": local_hour,
        "work_hours_local": [work_start, work_end],
        "in_work_window": in_work_window,
        "availability_multiplier": availability_multiplier,
        "baseline": {
            "response_delay_seconds": baseline_delay,
            "politeness": baseline_politeness,
            "terseness": baseline_terseness,
            "punctuation": baseline_punctuation,
            "directness": baseline_directness,
        },
        "persona_traits": persona_traits,
        "persona_source": persona_source,
        "affective_prior": affective_prior,
        "affective_prior_source": affective_prior_source,
        "affective_prior_weight": affective_prior_weight,
    }


def normalize_payload(payload: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    diagnostics: dict[str, Any] = {"degraded": False, "degradation_reasons": []}
    if not isinstance(payload, dict):
        mark_degraded(diagnostics, "payload_not_mapping")
        payload = {}
    normalized = dict(payload)
    message = normalized.get("message", "")
    if message is None:
        message = ""
    elif not isinstance(message, str):
        mark_degraded(diagnostics, "message_coerced_to_string")
        message = str(message)
    normalized["message"] = message
    normalized["context"] = as_mapping(normalized.get("context"), diagnostics, "context_not_mapping")
    normalized["runtime"] = as_mapping(normalized.get("runtime"), diagnostics, "runtime_not_mapping")
    user_profile = as_mapping(normalized.get("user_profile"), diagnostics, "user_profile_not_mapping")
    if user_profile:
        user_profile = dict(user_profile)
        user_profile["baseline"] = as_mapping(user_profile.get("baseline"), diagnostics, "user_profile.baseline_not_mapping")
        user_profile["persona_traits"] = as_mapping(user_profile.get("persona_traits"), diagnostics, "user_profile.persona_traits_not_mapping")
        user_profile["big5"] = as_mapping(user_profile.get("big5"), diagnostics, "user_profile.big5_not_mapping")
        user_profile["affective_prior"] = as_mapping(user_profile.get("affective_prior"), diagnostics, "user_profile.affective_prior_not_mapping")
    normalized["user_profile"] = user_profile
    last_state = as_mapping(normalized.get("last_state"), diagnostics, "last_state_not_mapping")
    if last_state:
        last_state = dict(last_state)
        last_state["vector"] = as_mapping(last_state.get("vector"), diagnostics, "last_state.vector_not_mapping")
        last_state["emotion_vector"] = as_mapping(last_state.get("emotion_vector"), diagnostics, "last_state.emotion_vector_not_mapping")
    normalized["last_state"] = last_state
    for key in ("llm_semantic", "review_semantic", "posthoc_semantic"):
        semantic = as_mapping(normalized.get(key), diagnostics, f"{key}_not_mapping")
        if semantic:
            semantic = dict(semantic)
            semantic["vector"] = as_mapping(semantic.get("vector"), diagnostics, f"{key}.vector_not_mapping")
            semantic["emotion_vector"] = as_mapping(semantic.get("emotion_vector"), diagnostics, f"{key}.emotion_vector_not_mapping")
            semantic["labels"] = canonicalize_labels(normalize_string_list(semantic.get("labels"), diagnostics, f"{key}.labels_not_list"))
        normalized[key] = semantic
    normalized["calibration_state"] = as_mapping(normalized.get("calibration_state"), diagnostics, "calibration_state_not_mapping")
    normalized["host_capabilities"] = as_mapping(normalized.get("host_capabilities"), diagnostics, "host_capabilities_not_mapping")
    normalized["history"] = normalize_history(normalized.get("history"), diagnostics)
    return normalized, diagnostics


def build_features(payload: dict[str, Any], diagnostics: dict[str, Any]) -> FeatureMap:
    message = str(payload.get("message") or "")
    history = payload.get("history") or []
    runtime = payload.get("runtime") or {}
    context = payload.get("context") or {}
    user_profile = load_user_profile(payload, diagnostics)
    language_hint = normalize_language_hint(context.get("language") or runtime.get("language"))
    if language_hint and language_hint in SUPPORTED_OUTPUT_LANGUAGES:
        language = language_hint
    elif language_hint:
        mark_degraded(diagnostics, f"unsupported_language:{language_hint}")
        language = "en"
    else:
        language = detect_language(message)
    norm_message = normalize_text(message)
    recent_users = recent_user_messages(history)
    previous_users = recent_users[:-1] if recent_users and normalize_text(recent_users[-1]) == norm_message else recent_users
    last_assistant = last_assistant_message(history)
    norm_last_assistant = normalize_text(last_assistant)

    chars = len(message.strip())
    words = len(re.findall(r"[A-Za-z0-9_./:-]+|[\u4e00-\u9fff]", message))
    questions = message.count("?") + message.count("？")
    exclamations = message.count("!") + message.count("！")
    ellipsis = message.count("...") + message.count("……") + message.count("…")
    uppercase_tokens = len(re.findall(r"\b[A-Z]{2,}\b", message))
    code_markers = int("```" in message or "`" in message or bool(re.search(r"\b[A-Za-z_]+\.[A-Za-z0-9_]+\b", message)))
    file_refs = len(re.findall(r"[A-Za-z0-9_./\\-]+\.[A-Za-z0-9_]+", message))
    list_markers = len(re.findall(r"\b\d+\.", message)) + len(re.findall(r"[;；、]", message))
    punctuation_runs = len(PUNCT_RUN_PATTERN.findall(message))
    latin_elongations = len(LATIN_ELONGATION_PATTERN.findall(message))
    cjk_elongations = len(CJK_ELONGATION_PATTERN.findall(message))
    mixed_script_runs = len(MIXED_SCRIPT_PATTERN.findall(message))
    no_space_punct_runs = len(NO_SPACE_PUNCT_PATTERN.findall(message))
    spaced_pause_runs = len(SPACED_DOTS_PATTERN.findall(message))
    double_dot_runs = len(DOUBLE_DOT_PATTERN.findall(message))
    case_shift_runs = len(CASE_SHIFT_PATTERN.findall(message))
    token_repeat_runs = len(TOKEN_REPEAT_PATTERN.findall(message))
    half_sentence_cut = 1.0 if HALF_SENTENCE_CUT_PATTERN.search(message) else 0.0
    abrupt_period_reply = 1.0 if (ABRUPT_EN_PATTERN.match(message) or ABRUPT_ZH_PATTERN.match(message)) else 0.0

    anger_hits = count_terms(message, ANGER_TERMS)
    urgency_hits = count_terms(message, URGENCY_TERMS)
    soft_urgency_hits = count_terms(message, SOFT_URGENCY_TERMS)
    rush_typo_hits = count_hybrid_terms(message, RUSH_TYPO_TERMS)
    textism_hits = count_token_terms(message, TEXTISM_TERMS)
    nonstandard_spelling_hits = count_token_terms(message, NONSTANDARD_SPELLING_TERMS)
    frustration_hits = count_terms(message, FRUSTRATION_TERMS)
    stall_hits = count_terms(message, STALL_TERMS)
    confusion_hits = count_terms(message, CONFUSION_TERMS)
    satisfaction_hits = count_terms(message, SATISFACTION_TERMS)
    continue_hits = count_terms(message, CONTINUE_TERMS)
    blocking_hits = count_terms(message, BLOCKING_TERMS)
    caution_hits = count_terms(message, CAUTION_TERMS)
    boundary_hits = count_terms(message, BOUNDARY_TERMS)
    assurance_hits = count_terms(message, ASSURANCE_TERMS)
    skepticism_hits = count_terms(message, SKEPTICISM_TERMS)
    speculation_hits = count_terms(message, SPECULATION_TERMS)
    context_loss_hits = count_terms(message, CONTEXT_LOSS_TERMS)
    execution_plumbing_hits = count_terms(message, EXECUTION_PLUMBING_TERMS)
    hedge_hits = count_terms(message, HEDGE_TERMS)
    dismissive_hits = count_terms(message, DISMISSIVE_TERMS)
    praise_hits = count_terms(message, PRAISE_TERMS)
    polite_hits = count_terms(message, POLITE_TERMS)
    explore_hits = count_terms(message, EXPLORATION_TERMS)
    command_hits = count_terms(message, COMMAND_TERMS)
    vague_hits = count_terms(message, VAGUE_TERMS)
    task_object_hits = count_terms(message, TASK_OBJECT_TERMS)
    success_hits = count_terms(message, SUCCESS_TERMS)
    guard_hits = count_terms(message, GUARD_TERMS)
    missed_expectation_hits = count_terms(message, MISSED_EXPECTATION_TERMS)
    technical_hits = count_terms(message, TECHNICAL_TERMS)
    evidence_request = 1.0 if EVIDENCE_REQUEST_PATTERN.search(norm_message) else 0.0
    comparison_request = 1.0 if COMPARISON_REQUEST_PATTERN.search(norm_message) else 0.0
    guardrail_request = 1.0 if GUARDRAIL_REQUEST_PATTERN.search(norm_message) else 0.0
    explicit_confusion_request = 1.0 if EXPLICIT_CONFUSION_PATTERN.search(norm_message) else 0.0
    if STILL_BROKEN_PATTERN.search(norm_message):
        success_hits = 0

    repeat_similarity = max_similarity(message, previous_users)
    short_burst = 1.0 if chars <= 18 else 0.75 if chars <= 48 else 0.35 if chars <= 120 else 0.1
    question_units = 1 if questions and confusion_hits == 0 and re.search(r"[?？]{2,}", message) else questions
    question_density = clamp(ratio(question_units, max(chars, 1)) * 22.0)
    exclamation_pressure = clamp(exclamations / 3.0)
    uppercase_pressure = clamp(uppercase_tokens / 2.0)
    vague_ratio = clamp(vague_hits / 3.0)
    technical_ratio = clamp(technical_hits / 5.0)
    command_ratio = clamp(command_hits / 3.0)
    praise_ratio = clamp((praise_hits + satisfaction_hits) / 4.0)
    polite_ratio = clamp(polite_hits / 3.0)
    explore_ratio = clamp((explore_hits + 1.3 * comparison_request) / 3.0)
    task_object_ratio = clamp(task_object_hits / 3.0)
    success_ratio = clamp(success_hits / 3.0)
    continue_ratio = clamp(continue_hits / 3.0)
    blocking_ratio = clamp(blocking_hits / 3.0)
    caution_ratio = clamp((caution_hits + 1.1 * guardrail_request) / 3.0)
    boundary_ratio = clamp((boundary_hits + 0.9 * guardrail_request) / 3.0)
    assurance_ratio = clamp((assurance_hits + 0.7 * evidence_request + 0.8 * guardrail_request) / 3.0)
    skepticism_ratio = clamp((skepticism_hits + 1.25 * evidence_request) / 3.0)
    speculation_ratio = clamp(speculation_hits / 3.0)
    context_loss_ratio = clamp(context_loss_hits / 3.0)
    execution_plumbing_ratio = clamp(execution_plumbing_hits / 3.0)
    hedge_ratio = clamp(hedge_hits / 2.0)
    dismissive_ratio = clamp(dismissive_hits / 3.0)
    textism_ratio = clamp(textism_hits / 4.0)
    nonstandard_spelling_ratio = clamp(nonstandard_spelling_hits / 4.0)
    guard_ratio = clamp(guard_hits / 3.0)
    missed_expectation_ratio = clamp(missed_expectation_hits / 3.0)
    frustration_ratio = clamp(frustration_hits / 3.0)
    stall_ratio = clamp(stall_hits / 3.0)
    soft_correction = 1.0 if SOFT_CORRECTION_PATTERN.search(message) and (hedge_hits >= 1 or skepticism_hits >= 1) else 0.0
    punctuation_pressure = clamp(
        0.36 * clamp(punctuation_runs / 2.0)
        + 0.22 * exclamation_pressure
        + 0.16 * question_density
        + 0.18 * clamp((latin_elongations + cjk_elongations) / 2.0)
        + 0.08 * clamp(ellipsis / 2.0)
    )
    tempo_pause_ratio = clamp(
        0.32 * clamp((ellipsis + spaced_pause_runs + double_dot_runs) / 3.0)
        + 0.22 * half_sentence_cut
        + 0.18 * clamp(token_repeat_runs / 2.0)
        + 0.14 * clamp(case_shift_runs / 2.0)
        + 0.14 * clamp(punctuation_runs / 2.0)
    )
    goal_specificity = clamp(
        0.3 * technical_ratio
        + 0.24 * command_ratio
        + 0.16 * task_object_ratio
        + 0.18 * clamp(file_refs / 2.0)
        + 0.12 * clamp(code_markers)
        + 0.08 * success_ratio
        + 0.08 * evidence_request
        + 0.1 * comparison_request
        + 0.1 * guardrail_request
        + 0.06 * boundary_ratio
        + 0.04 * assurance_ratio
    )
    typing_chaos = clamp(
        0.34 * clamp(rush_typo_hits / 2.0)
        + 0.26 * clamp(mixed_script_runs / 2.0)
        + 0.2 * clamp(no_space_punct_runs / 2.0)
        + 0.1 * clamp((latin_elongations + cjk_elongations) / 2.0)
        + 0.1 * short_burst
    )

    response_delay_seconds = safe_float(runtime.get("response_delay_seconds"), 0.0, diagnostics, "runtime.response_delay_seconds_invalid")
    unresolved_turns = safe_float(runtime.get("unresolved_turns"), 0.0, diagnostics, "runtime.unresolved_turns_invalid")
    bug_retries = safe_float(runtime.get("bug_retries"), 0.0, diagnostics, "runtime.bug_retries_invalid")
    task_age_minutes = safe_float(runtime.get("task_age_minutes"), 0.0, diagnostics, "runtime.task_age_minutes_invalid")
    queue_depth = safe_float(runtime.get("queue_depth"), 0.0, diagnostics, "runtime.queue_depth_invalid")
    background_tasks_running = safe_float(runtime.get("background_tasks_running"), 0.0, diagnostics, "runtime.background_tasks_running_invalid")
    same_issue_mentions = safe_float(runtime.get("same_issue_mentions"), 0.0, diagnostics, "runtime.same_issue_mentions_invalid")
    contradiction_signal = clamp(safe_float(runtime.get("contradiction_signal"), 0.0, diagnostics, "runtime.contradiction_signal_invalid"))
    raw_last_outcome = runtime.get("last_routing_outcome")
    if raw_last_outcome is None:
        last_routing_outcome: dict[str, Any] = {}
    elif isinstance(raw_last_outcome, dict):
        last_routing_outcome = raw_last_outcome
    else:
        mark_degraded(diagnostics, "runtime.last_routing_outcome_not_mapping")
        last_routing_outcome = {}
    outcome_text = normalize_text(str(last_routing_outcome.get("user_followed_up_with") or last_routing_outcome.get("result") or ""))
    last_outcome_success = 1.0 if outcome_text in {"thanks", "works", "resolved", "success", "accepted", "done"} or CLAIMED_RESOLUTION_PATTERN.search(outcome_text) else 0.0
    last_outcome_retry = 1.0 if outcome_text in {"still broken", "same issue", "failed", "not fixed", "retry"} or STILL_BROKEN_PATTERN.search(outcome_text) else 0.0
    last_outcome_complaint = 1.0 if outcome_text in {"explicit_complaint", "complaint", "bad", "worse"} else 0.0
    resolution_claimed = 1.0 if CLAIMED_RESOLUTION_PATTERN.search(norm_last_assistant) else 0.0
    resolution_mismatch = 1.0 if resolution_claimed and STILL_BROKEN_PATTERN.search(norm_message) else 0.0

    effective_delay_budget_seconds = user_profile["baseline"]["response_delay_seconds"] * float(user_profile["availability_multiplier"])
    delay_pressure = clamp(response_delay_seconds / max(12.0, effective_delay_budget_seconds))
    stuck_pressure = clamp(
        (unresolved_turns * 0.16)
        + (bug_retries * 0.24)
        + (task_age_minutes / 75.0)
        + (same_issue_mentions * 0.18)
        + (stall_ratio * 0.14)
        + (repeat_similarity * 0.12)
        + (resolution_mismatch * 0.08)
        + (last_outcome_retry * 0.2)
        + (last_outcome_complaint * 0.16)
        - (last_outcome_success * 0.08)
    )
    if soft_urgency_hits and (delay_pressure >= 0.34 or stall_hits >= 1 or blocking_hits >= 1 or frustration_hits >= 1 or stuck_pressure >= 0.42):
        urgency_hits += soft_urgency_hits
    background_pressure = clamp((queue_depth * 0.2) + (background_tasks_running * 0.15))
    politeness_delta = clamp(polite_ratio - user_profile["baseline"]["politeness"] + 0.15)
    terseness_delta = clamp(short_burst - user_profile["baseline"]["terseness"] + 0.15)
    punctuation_delta = clamp(punctuation_pressure - user_profile["baseline"]["punctuation"] + 0.15)
    directness_delta = clamp(command_ratio - user_profile["baseline"]["directness"] + 0.15)
    abrupt_delta = clamp(abrupt_period_reply * (1.0 - 0.55 * user_profile["baseline"]["terseness"]))
    surface_signal_reliability = clamp(
        0.28 * delay_pressure
        + 0.24 * stuck_pressure
        + 0.18 * repeat_similarity
        + 0.12 * contradiction_signal
        + 0.1 * goal_specificity
        + 0.08 * blocking_ratio
        + 0.08 * context_loss_ratio
        + 0.08 * execution_plumbing_ratio
    )
    dismissive_pressure = clamp(dismissive_ratio * (0.34 + 0.66 * surface_signal_reliability))
    tempo_pause_pressure = clamp(tempo_pause_ratio * (0.38 + 0.62 * max(delay_pressure, stall_ratio, frustration_ratio, skepticism_ratio, blocking_ratio)))
    textism_pressure = clamp(
        (0.56 * textism_ratio + 0.44 * nonstandard_spelling_ratio)
        * (0.32 + 0.68 * max(delay_pressure, short_burst, clamp(urgency_hits / 2.0), directness_delta))
    )
    surface_only_pressure = clamp(0.42 * dismissive_ratio + 0.3 * textism_ratio + 0.28 * tempo_pause_ratio)
    surface_uncertainty = clamp(surface_only_pressure * (1.0 - surface_signal_reliability))

    evidence: list[str] = []
    if urgency_hits:
        evidence.append("urgency_terms")
    if frustration_hits or anger_hits:
        evidence.append("frustration_terms")
    if stall_hits:
        evidence.append("stall_terms")
    if repeat_similarity >= 0.72:
        evidence.append("repeated_user_emphasis")
    if punctuation_pressure >= 0.36:
        evidence.append("punctuation_intensity")
    if typing_chaos >= 0.32:
        evidence.append("typing_chaos")
    if dismissive_pressure >= 0.28:
        evidence.append("dismissive_cue")
    if tempo_pause_pressure >= 0.3:
        evidence.append("tempo_pause_cue")
    if textism_pressure >= 0.28:
        evidence.append("textism_cue")
    if abrupt_period_reply:
        evidence.append("abrupt_short_reply")
    if task_object_ratio >= 0.24:
        evidence.append("task_object_anchor")
    if evidence_request >= 1.0:
        evidence.append("evidence_request")
    if comparison_request >= 1.0:
        evidence.append("structured_compare")
    if delay_pressure >= 0.35:
        evidence.append("delay_pressure")
    if stuck_pressure >= 0.42:
        evidence.append("stuck_issue_pressure")
    if guardrail_request >= 1.0:
        evidence.append("guardrail_request")
    if resolution_mismatch:
        evidence.append("resolution_mismatch")
    if last_outcome_retry or last_outcome_complaint:
        evidence.append("last_routing_outcome_retry")
    if last_outcome_success:
        evidence.append("last_routing_outcome_success")
    if guard_hits:
        evidence.append("guard_terms")
    if blocking_hits:
        evidence.append("blocking_terms")
    if caution_hits or boundary_hits or assurance_hits:
        evidence.append("boundary_terms")
    if skepticism_hits or hedge_hits or contradiction_signal >= 0.34:
        evidence.append("skepticism_terms")
    if speculation_ratio >= 0.24:
        evidence.append("guesswork_terms")
    if context_loss_ratio >= 0.24:
        evidence.append("context_loss_terms")
    if execution_plumbing_ratio >= 0.24:
        evidence.append("execution_plumbing_terms")
    if missed_expectation_ratio >= 0.24:
        evidence.append("missed_expectation")
    if technical_hits:
        evidence.append("technical_context")

    return {
        "message": message,
        "language": language,
        "chars": chars,
        "words": words,
        "questions": questions,
        "exclamations": exclamations,
        "ellipsis": ellipsis,
        "uppercase_tokens": uppercase_tokens,
        "code_markers": code_markers,
        "file_refs": file_refs,
        "list_markers": list_markers,
        "punctuation_runs": punctuation_runs,
        "latin_elongations": latin_elongations,
        "cjk_elongations": cjk_elongations,
        "mixed_script_runs": mixed_script_runs,
        "no_space_punct_runs": no_space_punct_runs,
        "spaced_pause_runs": spaced_pause_runs,
        "double_dot_runs": double_dot_runs,
        "case_shift_runs": case_shift_runs,
        "token_repeat_runs": token_repeat_runs,
        "half_sentence_cut": half_sentence_cut,
        "abrupt_period_reply": abrupt_period_reply,
        "anger_hits": anger_hits,
        "urgency_hits": urgency_hits,
        "rush_typo_hits": rush_typo_hits,
        "textism_hits": textism_hits,
        "nonstandard_spelling_hits": nonstandard_spelling_hits,
        "frustration_hits": frustration_hits,
        "stall_hits": stall_hits,
        "confusion_hits": confusion_hits,
        "satisfaction_hits": satisfaction_hits,
        "continue_hits": continue_hits,
        "blocking_hits": blocking_hits,
        "caution_hits": caution_hits,
        "boundary_hits": boundary_hits,
        "assurance_hits": assurance_hits,
        "skepticism_hits": skepticism_hits,
        "speculation_hits": speculation_hits,
        "context_loss_hits": context_loss_hits,
        "execution_plumbing_hits": execution_plumbing_hits,
        "hedge_hits": hedge_hits,
        "dismissive_hits": dismissive_hits,
        "praise_hits": praise_hits,
        "polite_hits": polite_hits,
        "explore_hits": explore_hits,
        "command_hits": command_hits,
        "vague_hits": vague_hits,
        "task_object_hits": task_object_hits,
        "success_hits": success_hits,
        "guard_hits": guard_hits,
        "missed_expectation_hits": missed_expectation_hits,
        "technical_hits": technical_hits,
        "evidence_request": evidence_request,
        "comparison_request": comparison_request,
        "guardrail_request": guardrail_request,
        "explicit_confusion_request": explicit_confusion_request,
        "repeat_similarity": round(repeat_similarity, 4),
        "short_burst": short_burst,
        "question_density": round(question_density, 4),
        "exclamation_pressure": round(exclamation_pressure, 4),
        "uppercase_pressure": round(uppercase_pressure, 4),
        "vague_ratio": round(vague_ratio, 4),
        "technical_ratio": round(technical_ratio, 4),
        "command_ratio": round(command_ratio, 4),
        "praise_ratio": round(praise_ratio, 4),
        "polite_ratio": round(polite_ratio, 4),
        "politeness_delta": round(politeness_delta, 4),
        "explore_ratio": round(explore_ratio, 4),
        "task_object_ratio": round(task_object_ratio, 4),
        "success_ratio": round(success_ratio, 4),
        "continue_ratio": round(continue_ratio, 4),
        "blocking_ratio": round(blocking_ratio, 4),
        "caution_ratio": round(caution_ratio, 4),
        "boundary_ratio": round(boundary_ratio, 4),
        "assurance_ratio": round(assurance_ratio, 4),
        "skepticism_ratio": round(skepticism_ratio, 4),
        "speculation_ratio": round(speculation_ratio, 4),
        "context_loss_ratio": round(context_loss_ratio, 4),
        "execution_plumbing_ratio": round(execution_plumbing_ratio, 4),
        "hedge_ratio": round(hedge_ratio, 4),
        "dismissive_ratio": round(dismissive_ratio, 4),
        "textism_ratio": round(textism_ratio, 4),
        "nonstandard_spelling_ratio": round(nonstandard_spelling_ratio, 4),
        "guard_ratio": round(guard_ratio, 4),
        "missed_expectation_ratio": round(missed_expectation_ratio, 4),
        "frustration_ratio": round(frustration_ratio, 4),
        "stall_ratio": round(stall_ratio, 4),
        "soft_correction": round(soft_correction, 4),
        "punctuation_pressure": round(punctuation_pressure, 4),
        "tempo_pause_ratio": round(tempo_pause_ratio, 4),
        "typing_chaos": round(typing_chaos, 4),
        "punctuation_delta": round(punctuation_delta, 4),
        "terseness_delta": round(terseness_delta, 4),
        "directness_delta": round(directness_delta, 4),
        "abrupt_delta": round(abrupt_delta, 4),
        "surface_signal_reliability": round(surface_signal_reliability, 4),
        "dismissive_pressure": round(dismissive_pressure, 4),
        "tempo_pause_pressure": round(tempo_pause_pressure, 4),
        "textism_pressure": round(textism_pressure, 4),
        "surface_only_pressure": round(surface_only_pressure, 4),
        "surface_uncertainty": round(surface_uncertainty, 4),
        "goal_specificity": round(goal_specificity, 4),
        "effective_delay_budget_seconds": round(effective_delay_budget_seconds, 4),
        "response_delay_seconds": response_delay_seconds,
        "unresolved_turns": unresolved_turns,
        "bug_retries": bug_retries,
        "task_age_minutes": task_age_minutes,
        "queue_depth": queue_depth,
        "background_tasks_running": background_tasks_running,
        "same_issue_mentions": same_issue_mentions,
        "contradiction_signal": contradiction_signal,
        "resolution_claimed": resolution_claimed,
        "resolution_mismatch": resolution_mismatch,
        "last_routing_outcome": last_routing_outcome,
        "last_outcome_success": last_outcome_success,
        "last_outcome_retry": last_outcome_retry,
        "last_outcome_complaint": last_outcome_complaint,
        "delay_pressure": round(delay_pressure, 4),
        "stuck_pressure": round(stuck_pressure, 4),
        "background_pressure": round(background_pressure, 4),
        "user_profile": user_profile,
        "evidence": evidence,
    }
