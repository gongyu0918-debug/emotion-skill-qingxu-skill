from __future__ import annotations

import json
from typing import Any

from emotion_types import *
from emotion_utils import *


def build_system_prompt_addendum(features: dict[str, Any], confirmed: dict[str, Any], prediction: dict[str, Any]) -> str:
    mode = confirmed["dominant_mode"]
    language = features["language"]
    if language == "zh":
        if mode in {"urgent", "frustrated"}:
            return "用户已经多次尝试。先确认当前最小复现检查点，再给出一个带明确成功判据的下一步。保持进度可见。"
        if mode == "skeptical":
            return "用户希望先看到依据。回复以校验点、命令或日志片段开头，再给结论和下一步。"
        if mode == "confused":
            return "用户需要目标对齐。先用一句话复述你理解的目标，再给一个可纠正的默认路径。"
        if mode == "cautious":
            return "默认保护现有可工作状态。任何变更前先说明范围、校验点和回滚路径。"
        if mode == "satisfied" or prediction["guard_needed"]:
            return "保留当前可工作状态。优先做回归检查、交付说明和收口，避免扩展 scope。"
        return "给出一个具体建议，说明下一步和验证方式。"
    if mode in {"urgent", "frustrated"}:
        return "The user has tried this path multiple times. Confirm the smallest reproducible checkpoint, then give one next action with a clear success criterion. Keep progress visible."
    if mode == "skeptical":
        return "The user wants evidence before more changes. Start with a verification point, command, or log excerpt, then give the conclusion and next step."
    if mode == "confused":
        return "The user needs goal alignment. Restate the target in one sentence, then give one correctable default path."
    if mode == "cautious":
        return "Protect the current working state by default. Before any change, name the scope, verification point, and rollback path."
    if mode == "satisfied" or prediction["guard_needed"]:
        return "Preserve the working state. Prioritize regression checks, handoff notes, and closeout before adding scope."
    return "Give one concrete recommendation, the next step, and the verification method."


def guidance_tone(mode: str) -> str:
    if mode in {"urgent", "frustrated"}:
        return "concise_and_concrete"
    if mode == "skeptical":
        return "evidence_first"
    if mode == "cautious":
        return "careful_and_bounded"
    if mode == "confused":
        return "alignment_first"
    if mode == "satisfied":
        return "guarded_closeout"
    return "direct_and_useful"


def build_guidance(features: dict[str, Any], confirmed: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    mode = confirmed["dominant_mode"]
    language = features["language"]
    system_prompt_addendum = build_system_prompt_addendum(features, confirmed, prediction)
    tone = guidance_tone(mode)
    should_probe = prediction["probe_needed"]
    allow_emotion_hook = bool(should_probe and mode not in {"urgent", "frustrated", "skeptical"} and prediction["frustration_risk"] < 0.7)
    if not should_probe:
        return {
            "should_probe": False,
            "allow_emotion_hook": False,
            "probe_style": "none",
            "hook_mode": "none",
            "tone": tone,
            "system_prompt_addendum": system_prompt_addendum,
            "soft_probe_seed": "",
            "question": "",
            "reason": "state already clear enough",
        }
    if language == "zh":
        if mode in {"urgent", "frustrated"}:
            question = "先给结果，还是先给报错定位？"
            probe_style = "priority_axis"
            hook_mode = "explicit"
            soft_probe_seed = ""
        elif mode == "confused":
            question = ""
            probe_style = "latent_preference_probe"
            hook_mode = "latent"
            soft_probe_seed = "在首句加入可纠正默认项，例如“我先按一条可落地路径推进”，引导用户自然暴露偏好。"
        elif mode == "skeptical":
            question = ""
            probe_style = "latent_evidence_probe"
            hook_mode = "latent"
            soft_probe_seed = "首句先给依据和校验点，再给动作，让用户自然暴露证据偏好。"
        elif mode == "cautious":
            question = ""
            probe_style = "latent_boundary_probe"
            hook_mode = "latent"
            soft_probe_seed = "在首句先复述安全边界并给出保守默认项，让用户自然补充禁止项。"
        elif prediction["guard_needed"]:
            question = ""
            probe_style = "latent_guard_probe"
            hook_mode = "latent"
            soft_probe_seed = "在首句写成“我先按已达标进入收口检查”，让用户自然选择继续推进或结束。"
        else:
            question = ""
            probe_style = "latent_choice_probe"
            hook_mode = "latent"
            soft_probe_seed = "在首段同时放一个主建议和一个备选方向词，引导用户自然偏向其一。"
    else:
        if mode in {"urgent", "frustrated"}:
            question = "Fix first, or diagnosis first?"
            probe_style = "priority_axis"
            hook_mode = "explicit"
            soft_probe_seed = ""
        elif mode == "confused":
            question = ""
            probe_style = "latent_preference_probe"
            hook_mode = "latent"
            soft_probe_seed = "Open with a default path such as 'I will start with one concrete path' so the user can correct it naturally."
        elif mode == "skeptical":
            question = ""
            probe_style = "latent_evidence_probe"
            hook_mode = "latent"
            soft_probe_seed = "Lead with the basis and one concrete verification point before the action plan."
        elif mode == "cautious":
            question = ""
            probe_style = "latent_boundary_probe"
            hook_mode = "latent"
            soft_probe_seed = "State a conservative safety assumption in the first line so the user can refine boundaries without a hard stop."
        elif prediction["guard_needed"]:
            question = ""
            probe_style = "latent_guard_probe"
            hook_mode = "latent"
            soft_probe_seed = "Frame the next step as a guard-mode default so the user can continue or close naturally."
        else:
            question = ""
            probe_style = "latent_choice_probe"
            hook_mode = "latent"
            soft_probe_seed = "Lead with one recommendation and mention one soft alternative to invite natural preference disclosure."
    return {
        "should_probe": True,
        "allow_emotion_hook": allow_emotion_hook,
        "probe_style": probe_style,
        "hook_mode": hook_mode,
        "tone": tone,
        "system_prompt_addendum": system_prompt_addendum,
        "soft_probe_seed": soft_probe_seed if allow_emotion_hook else "",
        "question": question,
        "reason": "clarity is low or frustration risk is rising",
    }


def build_posthoc_plan(features: dict[str, Any], confirmed: dict[str, Any], analysis: dict[str, Any], weight_schedule: dict[str, Any]) -> dict[str, Any]:
    mode = confirmed["dominant_mode"]
    stage = weight_schedule["stage"]
    low_signal = confirmed["confidence"] < 0.64 or analysis["ambiguity"] >= 0.22
    weak_shift = bool(features["skepticism_ratio"] >= 0.25 or features["hedge_ratio"] >= 0.25 or features["assurance_ratio"] >= 0.25 or features["dismissive_pressure"] >= 0.26 or features["tempo_pause_pressure"] >= 0.28 or features["questions"] >= 1)
    low_consistency = weight_schedule["effective_consistency"] <= 0.58
    should_run = True
    if stage == "bootstrap" or weight_schedule["effective_consistency"] <= 0.38:
        style = "full_decompose"
        max_response_tokens = 180
        target_ms = 550
        reason = "bootstrap review pass stays enabled while consistency is still cold"
    elif stage == "calibrating" or low_consistency or low_signal or weak_shift or mode in {"confused", "skeptical"}:
        style = "compact_decompose"
        max_response_tokens = 110
        target_ms = 360
        reason = "calibration still benefits from a richer review pass"
    else:
        style = "micro_reflection"
        max_response_tokens = 56
        target_ms = 140
        reason = "front-versus-review agreement is stable so the review pass stays compact"
    return {
        "should_run": should_run,
        "execution_mode": "shadow_review",
        "surface": "runtime_internal",
        "style": style,
        "target_ms": target_ms,
        "max_response_tokens": max_response_tokens,
        "weight": weight_schedule["posthoc_weight"],
        "reason": reason,
    }


def render_overlay(features: dict[str, Any], confirmed: dict[str, Any], prediction: dict[str, Any], routing: dict[str, Any], analysis: dict[str, Any]) -> str:
    signal_alias = {
        "urgency_terms": "urg",
        "frustration_terms": "frus",
        "stall_terms": "stall",
        "repeated_user_emphasis": "repeat",
        "punctuation_intensity": "punct",
        "dismissive_cue": "dismiss",
        "tempo_pause_cue": "tempo",
        "textism_cue": "textism",
        "abrupt_short_reply": "abrupt",
        "task_object_anchor": "task",
        "delay_pressure": "delay",
        "stuck_issue_pressure": "stuck",
        "resolution_mismatch": "mismatch",
        "guard_terms": "guard",
        "boundary_terms": "bound",
        "skepticism_terms": "skept",
        "evidence_request": "proof",
        "structured_compare": "compare",
        "guardrail_request": "guardreq",
        "technical_context": "tech",
    }
    actions: list[str] = []
    mode = confirmed["dominant_mode"]
    if mode in {"urgent", "frustrated"}:
        actions.extend(["act-first", "short-first-reply"])
    elif mode == "confused":
        actions.extend(["stepwise", "one-clarifier-max"])
    elif mode == "skeptical":
        actions.extend(["show-basis", "light-proof"])
    elif mode == "satisfied":
        actions.extend(["guard-mode", "drift-check"])
    elif mode == "cautious":
        actions.extend(["verify-first", "keep-scope-tight"])
    else:
        actions.extend(["decisive", "expand-only-if-useful"])
    signals = ",".join(signal_alias.get(item, item) for item in analysis["priority_reason"][:2]) if analysis["priority_reason"] else mode
    return (
        f"<state mode={mode} route={routing['thread_interface']['queue_mode']} "
        f"main={1 if routing['thread_interface']['prefer_main_thread'] else 0} "
        f"hb={'defer' if routing['thread_interface']['defer_heartbeat'] else 'normal'} "
        f"parallel={1 if routing['thread_interface']['allow_parallel_subagents'] else 0} "
        f"style={routing['reply_style']} verify={routing['verification_level']} "
        f"upd={routing['thread_interface']['progress_update_interval_sec']}s "
        f"probe={1 if prediction['probe_needed'] else 0} "
        f"sem={analysis['semantic_pass']}>\n"
        f"signals:{signals}; actions:{','.join(actions)}\n"
        "</state>"
    )


def render_debug_overlay(features: dict[str, Any], confirmed: dict[str, Any], prediction: dict[str, Any], routing: dict[str, Any], analysis: dict[str, Any]) -> str:
    return (
        "<emotion_context>\n"
        f"mode: {confirmed['dominant_mode']}\n"
        f"labels: {', '.join(confirmed['labels'])}\n"
        f"emotion_vector: {json.dumps(confirmed['emotion_vector'], ensure_ascii=False, separators=(',', ':'))}\n"
        f"confidence: {confirmed['confidence']}\n"
        f"reply_style: {routing['reply_style']}\n"
        f"verification_level: {routing['verification_level']}\n"
        f"queue_mode: {routing['thread_interface']['queue_mode']}\n"
        f"prefer_main_thread: {str(routing['thread_interface']['prefer_main_thread']).lower()}\n"
        f"defer_heartbeat: {str(routing['thread_interface']['defer_heartbeat']).lower()}\n"
        f"progress_update_interval_sec: {routing['thread_interface']['progress_update_interval_sec']}\n"
        f"frustration_risk: {prediction['frustration_risk']}\n"
        f"task_complexity: {prediction['task_complexity']['level']}\n"
        f"semantic_pass: {analysis['semantic_pass']}\n"
        f"signals: {', '.join(analysis['priority_reason'])}\n"
        "</emotion_context>"
    )


def build_model_prompts(payload: dict[str, Any], features: FeatureMap, screen: ScreenState, confirmed: ConfirmedState, routing: RoutingState, prediction: dict[str, Any], analysis: dict[str, Any], weight_schedule: dict[str, Any], posthoc_plan: dict[str, Any]) -> dict[str, str]:
    latest = str(payload.get("message") or "").strip()[:160]
    history = payload.get("history") or []
    runtime = payload.get("runtime") or {}
    user_profile = features["user_profile"]
    history_excerpt = [{"r": item.get("role", ""), "t": str(item.get("text") or item.get("content") or "")[:80]} for item in history[-3:]]
    profile_hint = {
        "tz": user_profile["timezone"],
        "h": user_profile["local_hour"],
        "work": user_profile["in_work_window"],
        "delay": user_profile["baseline"]["response_delay_seconds"],
        "polite": user_profile["baseline"]["politeness"],
        "terse": user_profile["baseline"]["terseness"],
        "prior": user_profile["affective_prior"],
        "persona": user_profile["persona_traits"],
    }
    fast_screen_prompt = (
        "Classify current user work-state for an agent runtime.\n"
        "Prioritize delay against user baseline, same-issue pressure, hang/stuck wording, terse abrupt replies, dismissive short phrases, rhythmic pause cues, missed-expectation timing cues, success/guard signals, evidence-seeking skepticism, and anti-guesswork language.\n"
        "Return JSON only: {\"m\":\"urgent\",\"labels\":[\"urgent\"],\"vector\":{\"urgency\":0.0,\"frustration\":0.0,\"clarity\":0.0,\"satisfaction\":0.0,\"trust\":0.0,\"engagement\":0.0},\"emotion_vector\":{\"urgency\":0.0,\"frustration\":0.0,\"confusion\":0.0,\"skepticism\":0.0,\"satisfaction\":0.0,\"cautiousness\":0.0,\"openness\":0.0},\"why\":[\"delay\"]}\n"
        f"latest={latest}\n"
        f"hist={json.dumps(history_excerpt, ensure_ascii=False, separators=(',', ':'))}\n"
        f"usr={json.dumps(profile_hint, ensure_ascii=False, separators=(',', ':'))}\n"
        f"rt={json.dumps(runtime, ensure_ascii=False, separators=(',', ':'))}"
    )
    fast_confirmation_prompt = (
        "Fuse the rule screen with runtime pressure.\n"
        "Treat nonstandard punctuation, textisms, and deliberate misspellings as weak cues unless runtime pressure, retries, or contradiction support them.\n"
        "Return JSON only: {\"m\":\"urgent\",\"labels\":[\"urgent\"],\"conf\":0.0,\"vector\":{\"urgency\":0.0,\"frustration\":0.0,\"clarity\":0.0,\"satisfaction\":0.0,\"trust\":0.0,\"engagement\":0.0},\"emotion_vector\":{\"urgency\":0.0,\"frustration\":0.0,\"confusion\":0.0,\"skepticism\":0.0,\"satisfaction\":0.0,\"cautiousness\":0.0,\"openness\":0.0},\"acts\":[\"act-first\"]}\n"
        f"screen={json.dumps(screen, ensure_ascii=False, separators=(',', ':'))}\n"
        f"usr={json.dumps(profile_hint, ensure_ascii=False, separators=(',', ':'))}\n"
        f"rt={json.dumps(runtime, ensure_ascii=False, separators=(',', ':'))}"
    )
    review_pass_prompt = (
        "Run a runtime-only follow-up review for the latest user message.\n"
        "Decompose latent affect and stance cues for bounded calibration.\n"
        "Extract the exact wording, hedge, correction, punctuation, tempo clue, textism, deliberate typo, nonstandard spelling, or stance marker that carries emotion.\n"
        "Focus on weak shifts such as hedging, correction, doubt, evidence-seeking, anti-guesswork language, scope protection, frustration, urgency, satisfaction, openness, dismissive short replies, rhythmic pauses, and missed-expectation timing language.\n"
        "Return JSON only: "
        "{\"emotion_vector\":{\"urgency\":0.0,\"frustration\":0.0,\"confusion\":0.0,\"skepticism\":0.0,\"satisfaction\":0.0,\"cautiousness\":0.0,\"openness\":0.0},"
        "\"labels\":[\"skeptical\"],\"confidence\":0.0,\"emotionality\":0.0,"
        "\"composition\":{\"urgency\":0.0,\"frustration\":0.0,\"confusion\":0.0,\"skepticism\":0.0,\"satisfaction\":0.0,\"cautiousness\":0.0,\"openness\":0.0},"
        "\"cue_spans\":[{\"text\":\"不一定\",\"signal\":\"skepticism\",\"kind\":\"hedge\",\"strength\":0.4}],"
        "\"notes\":[\"light hedge\"]}\n"
        f"stage={weight_schedule['stage']}\n"
        f"front_weight={weight_schedule['screen_weight']}\n"
        f"posthoc_weight={weight_schedule['posthoc_weight']}\n"
        f"front_consistency={weight_schedule['effective_consistency']}\n"
        f"execution_mode={posthoc_plan['execution_mode']}\n"
        f"latest={latest}\n"
        f"hist={json.dumps(history_excerpt, ensure_ascii=False, separators=(',', ':'))}\n"
        f"usr={json.dumps(profile_hint, ensure_ascii=False, separators=(',', ':'))}\n"
        f"screen_labels={json.dumps(screen['labels'], ensure_ascii=False, separators=(',', ':'))}\n"
        f"posthoc_style={posthoc_plan['style']}"
    )
    return {
        "fast_screen_prompt": fast_screen_prompt,
        "fast_confirmation_prompt": fast_confirmation_prompt,
        "review_pass_prompt": review_pass_prompt,
        "posthoc_reflection_prompt": review_pass_prompt,
        "overlay_prompt": render_overlay(features, confirmed, prediction, routing, analysis),
    }


def raw_emotion_requested(full: dict[str, Any]) -> bool:
    capabilities = full.get("host_capabilities") or {}
    explicit_values = [capabilities.get(key) for key in RAW_HOST_CAPABILITY_KEYS if key in capabilities]
    if any(capability_disabled(value) for value in explicit_values):
        return False
    return any(capability_enabled(value) for value in explicit_values) or bool((full.get("cli_options") or {}).get("include_raw_emotion"))


def capability_enabled(value: Any) -> bool:
    if value is True or value == 1:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def capability_disabled(value: Any) -> bool:
    if value is False or value == 0:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"0", "false", "no", "off"}
    return False


def validate_interaction_needs(needs: list[str]) -> list[str]:
    valid: list[str] = []
    for need in unique_labels(needs):
        if need in INTERACTION_NEED_ENUM:
            valid.append(need)
    return valid[:3]


def build_host_state_delta(state_delta: dict[str, Any]) -> dict[str, Any]:
    dominant_shift = str(state_delta.get("dominant_shift", "changed"))
    interaction_delta = dict(state_delta.get("interaction") or {})
    interaction_needs: list[str] = []
    if interaction_delta.get("clarity", 0.0) <= -0.05:
        interaction_needs.append("alignment_check")
    if interaction_delta.get("trust", 0.0) <= -0.05:
        interaction_needs.append("evidence_first")
    if interaction_delta.get("engagement", 0.0) <= -0.05:
        interaction_needs.append("keep_progress_visible")
    return {
        "available": bool(state_delta.get("available")),
        "dominant_shift": STATE_SHIFT_ALIASES.get(dominant_shift, dominant_shift),
        "interaction": {
            "changed": bool(interaction_delta),
            "needs": validate_interaction_needs(interaction_needs),
        },
    }


def build_host_output(full: dict[str, Any]) -> dict[str, Any]:
    confirmed = full["confirmed_state"]
    routing = full["routing"]
    thread_interface = routing["thread_interface"]
    memory_update = full["memory_update"]
    emotion_vector = clamp_dict(confirmed.get("emotion_vector"), EMOTION_DIMS)
    interaction_state = clamp_dict(confirmed.get("interaction_state"), INTERACTION_DIMS)
    output = {
        "schema_version": full["schema_version"],
        "degraded": full["degraded"],
        "degradation_reasons": full["degradation_reasons"],
        "mode": confirmed["dominant_mode"],
        "confidence": confirmed["confidence"],
        "overlay_prompt": full["overlay_prompt"],
        "route_reasons": full["route_reasons"],
        "response_constraints": full["response_constraints"],
        "satisfaction_lock": full["satisfaction_lock"],
        "interaction_state": interaction_state,
        "routing": {
            "reply_style": routing["reply_style"],
            "verification_level": routing["verification_level"],
            "queue_mode": thread_interface["queue_mode"],
            "prefer_main_thread": thread_interface["prefer_main_thread"],
            "defer_heartbeat": thread_interface["defer_heartbeat"],
            "allow_parallel_subagents": thread_interface["allow_parallel_subagents"],
            "max_parallel_subagents": thread_interface["max_parallel_subagents"],
            "progress_update_interval_sec": thread_interface["progress_update_interval_sec"],
        },
        "guidance": {
            "should_probe": full["guidance"]["should_probe"],
            "hook_mode": full["guidance"]["hook_mode"],
            "probe_style": full["guidance"]["probe_style"],
            "tone": full["guidance"]["tone"],
            "system_prompt_addendum": full["guidance"]["system_prompt_addendum"],
            "question": full["guidance"]["question"],
            "soft_probe_seed": full["guidance"]["soft_probe_seed"],
        },
        "state": {
            "interaction_state": interaction_state,
            "_deprecated_alias": {
                "interaction_state": "top_level.interaction_state",
                "remove_after": "1.3",
            },
            "state_delta": build_host_state_delta(full["state_delta"]),
        },
        "memory": {
            "should_persist": memory_update["should_persist"],
            "host_profile_update_recommended": memory_update["host_profile_update_recommended"],
            "proposed_calibration_state": memory_update["proposed_calibration_state"],
        },
    }
    if raw_emotion_requested(full):
        output["diagnostics"] = {
            "internal": {
                "labels": confirmed["labels"],
                "emotion_vector": emotion_vector,
                "state_delta": full["state_delta"],
                "mode_scores": confirmed.get("mode_scores", {}),
            }
        }
    return output
