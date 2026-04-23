#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import community_long_tail_cases as long_tail
import emotion_engine as ee


REAL_WORLD_CASES = [
    {
        "id": "claude_code_regression_loop",
        "source": "https://github.com/anthropics/claude-code/issues/4520",
        "payload": {
            "message": "This is still not fixed. You edited files I explicitly said not to touch and now it loops again. Show me the exact basis before changing more files.",
            "runtime": {"response_delay_seconds": 28, "unresolved_turns": 4, "bug_retries": 3, "same_issue_mentions": 3, "contradiction_signal": 0.42},
        },
        "expected": {
            "labels_all": ["frustrated", "skeptical"],
            "queue_mode_in": ["steer", "interrupt"],
            "reply_style_in": ["repair_then_explain", "evidence_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "codex_still_not_fixed",
        "source": "https://github.com/openai/codex/issues/6603",
        "payload": {
            "message": "Pick up where you left off. This is still not fixed. Not this error. No response.",
            "runtime": {"response_delay_seconds": 24, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2},
        },
        "expected": {
            "labels_all": ["urgent", "frustrated"],
            "queue_mode_in": ["steer", "interrupt"],
            "reply_style_in": ["act_then_brief", "repair_then_explain"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "kilocode_auto_hang",
        "source": "https://github.com/Kilo-Org/kilocode/issues/3450",
        "payload": {
            "message": "CLI gets stuck on the logo screen in auto mode. I thought it was gone, then it reoccurred.",
            "runtime": {"response_delay_seconds": 18, "unresolved_turns": 2, "bug_retries": 1, "task_age_minutes": 20},
        },
        "expected": {
            "labels_all": ["frustrated"],
            "queue_mode_in": ["steer", "interrupt"],
            "reply_style_in": ["repair_then_explain"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "copilotkit_tool_runtime_glitch",
        "source": "https://github.com/CopilotKit/CopilotKit/issues/2504",
        "payload": {
            "message": "The agent stops responding mid tool call. If I force continue it gets stuck on tool_use ids without tool_result blocks. Handle the missing tool gracefully.",
            "runtime": {"response_delay_seconds": 16, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2},
        },
        "expected": {
            "mode_in": ["urgent", "frustrated", "skeptical"],
            "labels_all": ["urgent", "frustrated"],
            "queue_mode_in": ["steer", "interrupt"],
            "reply_style_in": ["act_then_brief", "repair_then_explain", "evidence_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "gemini_windows_regression",
        "source": "https://github.com/google-gemini/gemini-cli/issues/13734",
        "payload": {
            "message": "It worked perfectly yesterday. Auto-update broke it without warning. The error is misleading. Please verify the root cause before suggesting network fixes.",
            "runtime": {"response_delay_seconds": 12, "unresolved_turns": 2, "bug_retries": 1, "contradiction_signal": 0.34},
        },
        "expected": {
            "labels_all": ["frustrated", "skeptical"],
            "queue_mode_in": ["steer", "collect"],
            "reply_style_in": ["repair_then_explain", "evidence_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 25,
        },
    },
    {
        "id": "claude_gitbash_despite_config",
        "source": "https://github.com/anthropics/claude-code/issues/8674",
        "payload": {
            "message": "This fails despite correct configuration and multiple troubleshooting attempts. Show me the exact detection path before telling me to reinstall anything.",
            "runtime": {"response_delay_seconds": 9, "unresolved_turns": 2, "contradiction_signal": 0.44},
        },
        "expected": {
            "mode_in": ["skeptical", "cautious"],
            "labels_all": ["skeptical"],
            "queue_mode_in": ["collect", "steer"],
            "reply_style_in": ["evidence_then_act", "verify_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 25,
        },
    },
    {
        "id": "shared_context_scoped_social",
        "source": "https://www.reddit.com/r/AI_Agents/comments/1rx2s2y/shipped_an_ai_agent_last_month_real_users_broke/",
        "payload": {
            "message": "You need shared context here. Pure prompt guessing will not cut it. Verify the handoff path and keep the scope tight.",
            "runtime": {"response_delay_seconds": 12, "unresolved_turns": 2, "same_issue_mentions": 2, "contradiction_signal": 0.3},
        },
        "expected": {
            "mode_in": ["skeptical", "cautious"],
            "labels_all": ["skeptical", "cautious"],
            "queue_mode_in": ["collect", "steer"],
            "reply_style_in": ["evidence_then_act", "verify_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 25,
        },
    },
    {
        "id": "claude_posttooluse_never_executes",
        "source": "https://github.com/anthropics/claude-code/issues/6403",
        "payload": {
            "message": "I followed the docs exactly. Hooks work manually but automatic execution never fires. Show me why the trigger path is broken before another workaround.",
            "runtime": {"response_delay_seconds": 14, "unresolved_turns": 3, "bug_retries": 2, "contradiction_signal": 0.38},
        },
        "expected": {
            "labels_all": ["frustrated", "skeptical"],
            "queue_mode_in": ["steer", "collect"],
            "reply_style_in": ["repair_then_explain", "evidence_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 25,
        },
    },
    {
        "id": "copilot_codebase_guesswork_discussion",
        "source": "https://github.com/orgs/community/discussions/162634",
        "payload": {
            "message": "You only analyzed a fraction of the codebase and guessed the rest. Stop speculating, show your limits, and base the answer on what is actually in the repo.",
            "runtime": {"response_delay_seconds": 12, "unresolved_turns": 2, "bug_retries": 1, "contradiction_signal": 0.36},
        },
        "expected": {
            "labels_all": ["frustrated", "skeptical"],
            "queue_mode_in": ["collect", "steer"],
            "reply_style_in": ["evidence_then_act", "repair_then_explain"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 25,
        },
    },
    {
        "id": "reminder_late_again_social",
        "source": "https://www.reddit.com/r/ios/comments/1ihxvao/reminders_app_is_not_reminding_me_not_getting/",
        "payload": {
            "message": "The reminder showed up late again. I needed it earlier and the notification never came when it should have fired.",
            "runtime": {"response_delay_seconds": 20, "unresolved_turns": 2, "task_age_minutes": 180},
        },
        "expected": {
            "labels_all": ["urgent", "frustrated"],
            "queue_mode_in": ["steer", "interrupt"],
            "reply_style_in": ["act_then_brief", "repair_then_explain"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "reminder_reopen_breakage_social",
        "source": "https://www.reddit.com/r/GoogleKeep/comments/158jliu/reminders_not_working_anymore/",
        "payload": {
            "message": "The reminder disappears again as soon as I reopen the app. This keeps breaking the one thing I need it for.",
            "runtime": {"response_delay_seconds": 18, "unresolved_turns": 3, "same_issue_mentions": 1},
        },
        "expected": {
            "labels_all": ["urgent", "frustrated"],
            "queue_mode_in": ["steer", "interrupt"],
            "reply_style_in": ["act_then_brief", "repair_then_explain"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "silent_jobs_broke_for_days_social",
        "source": "https://www.reddit.com/r/SaaS/comments/1sb8esi/my_automated_background_jobs_silently_broke_for_3/",
        "payload": {
            "message": "My automated background jobs silently broke for days and nobody noticed because there was no alert. Show me where monitoring failed before another workaround.",
            "runtime": {"response_delay_seconds": 16, "unresolved_turns": 3, "bug_retries": 2, "contradiction_signal": 0.3},
        },
        "expected": {
            "labels_all": ["frustrated", "skeptical"],
            "queue_mode_in": ["steer", "collect"],
            "reply_style_in": ["repair_then_explain", "evidence_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 25,
        },
    },
    {
        "id": "gateway_silent_monitor_social",
        "source": "https://www.reddit.com/r/openclaw/comments/1rfn0kz/gateway_silently_dies_pattern_report_after_25/",
        "payload": {
            "message": "The gateway goes quiet for minutes at a time, the health monitor gets stuck too, and you only notice when everything is silent.",
            "runtime": {"response_delay_seconds": 27, "unresolved_turns": 2, "bug_retries": 1, "task_age_minutes": 120, "contradiction_signal": 0.28},
        },
        "expected": {
            "labels_all": ["frustrated", "skeptical"],
            "queue_mode_in": ["steer", "collect"],
            "reply_style_in": ["repair_then_explain", "evidence_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 25,
        },
    },
    {
        "id": "architecture_guardrail_social",
        "source": "https://github.com/anthropics/claude-code/issues/4520",
        "payload": {
            "message": "I already spent hours on this. Keep the architecture modular and stop collapsing everything into one method.",
            "runtime": {"response_delay_seconds": 30, "task_age_minutes": 90, "bug_retries": 3},
        },
        "expected": {
            "mode_in": ["frustrated", "cautious"],
            "labels_all": ["frustrated", "cautious"],
            "queue_mode_in": ["steer", "collect"],
            "reply_style_in": ["repair_then_explain", "verify_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 25,
        },
    },
    {
        "id": "diagnostic_dies_here_social",
        "source": "https://github.com/openai/codex/issues/6603",
        "payload": {
            "message": "Scan the file and tell me why it dies here.",
            "runtime": {"response_delay_seconds": 14, "unresolved_turns": 2, "same_issue_mentions": 1},
        },
        "expected": {
            "mode_in": ["urgent", "confused"],
            "labels_all": ["urgent", "confused"],
            "queue_mode_in": ["collect", "steer"],
            "reply_style_in": ["explain_then_act", "evidence_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 25,
        },
    },
    {
        "id": "zombie_cron_no_alert_social",
        "source": "https://www.reddit.com/r/sysadmin/comments/1n4qcld/how_do_you_catch_zombie_cron_jobs_that_hang_but_dont_fail/",
        "payload": {
            "message": "This cron job hung for hours, burned CPU, and sent no alert. I need the real failure path, not more guesswork.",
            "runtime": {"response_delay_seconds": 18, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2, "contradiction_signal": 0.34},
        },
        "expected": {
            "mode_in": ["frustrated", "skeptical"],
            "labels_all": ["frustrated"],
            "queue_mode_in": ["steer", "interrupt"],
            "reply_style_in": ["repair_then_explain", "evidence_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "claude_hooks_broken_again",
        "source": "https://github.com/anthropics/claude-code/issues/10814",
        "payload": {
            "message": "BROKEN AGAIN after yesterday's fix. Every hook now fails silently. Compare 2.0.30 against 2.0.31 before another workaround.",
            "runtime": {"response_delay_seconds": 17, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2, "contradiction_signal": 0.36},
        },
        "expected": {
            "labels_all": ["frustrated", "skeptical"],
            "queue_mode_in": ["steer", "interrupt"],
            "reply_style_in": ["repair_then_explain", "evidence_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "codex_wsl_still_broken",
        "source": "https://www.reddit.com/r/codex/comments/1ory453",
        "payload": {
            "message": "Status says it's back to normal, sure... still broken for me on WSL after restarts and reinstall.",
            "runtime": {"response_delay_seconds": 13, "unresolved_turns": 2, "bug_retries": 1, "contradiction_signal": 0.4},
        },
        "expected": {
            "labels_all": ["frustrated", "skeptical"],
            "queue_mode_in": ["steer", "collect"],
            "reply_style_in": ["repair_then_explain", "evidence_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 25,
        },
    },
    {
        "id": "gemini_feedback_hang",
        "source": "https://github.com/google-gemini/gemini-cli/discussions/7432",
        "payload": {
            "message": "No retry logic, no append mode, no clear error handling... whatever. At least surface the failure instead of hanging.",
            "runtime": {"response_delay_seconds": 18, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2},
        },
        "expected": {
            "labels_all": ["frustrated"],
            "queue_mode_in": ["steer", "interrupt"],
            "reply_style_in": ["repair_then_explain", "act_then_brief"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "openclaw_gateway_running_but_dead",
        "source": "https://www.reddit.com/r/openclaw/comments/1rfn0kz/gateway_silently_dies_pattern_report_after_25/",
        "payload": {
            "message": "Status says running but nothing works. Cron jobs hang forever, messages do not deliver, no alert.",
            "runtime": {"response_delay_seconds": 18, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2, "contradiction_signal": 0.42},
        },
        "expected": {
            "labels_all": ["urgent", "frustrated"],
            "queue_mode_in": ["steer", "interrupt"],
            "reply_style_in": ["repair_then_explain", "evidence_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "ci_rules_guesswork_social",
        "source": "https://www.reddit.com/r/SideProject/comments/1smhsv9/i_built_a_cli_that_audits_whether_ai_coding_tools/",
        "payload": {
            "message": "These tools keep guessing my CI rules and wasting time with fixes that pass locally but fail CI.",
            "runtime": {"response_delay_seconds": 12, "unresolved_turns": 2, "bug_retries": 1, "contradiction_signal": 0.34},
        },
        "expected": {
            "labels_all": ["skeptical"],
            "queue_mode_in": ["steer"],
            "reply_style_in": ["evidence_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "google_tasks_manual_refresh_social",
        "source": "https://www.reddit.com/r/googleassistant/comments/1c0dck1/google_tasks_not_working_properly_with_reminders/",
        "payload": {
            "message": "I needed this reminder for something important and there was no alert at all. If I manually open Tasks, it suddenly appears.",
            "runtime": {"response_delay_seconds": 20, "unresolved_turns": 2, "task_age_minutes": 120},
        },
        "expected": {
            "labels_all": ["urgent", "frustrated"],
            "queue_mode_in": ["steer", "interrupt"],
            "reply_style_in": ["repair_then_explain", "act_then_brief"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "bullmq_scheduler_goes_quiet",
        "source": "https://github.com/taskforcesh/bullmq/issues/3272",
        "payload": {
            "message": "CloudWatch stops receiving metrics because the scheduler silently stops producing jobs. It ends in drained and then just goes quiet.",
            "runtime": {"response_delay_seconds": 14, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2},
        },
        "expected": {
            "labels_all": ["frustrated"],
            "queue_mode_in": ["steer", "interrupt"],
            "reply_style_in": ["repair_then_explain"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "openclaw_context_loss_after_reset",
        "source": "https://www.reddit.com/r/openclaw/comments/1r3501p/solving_context_loss_after_compactionreset_a/",
        "payload": {
            "message": "After a compaction or a new session reset, the agent completely loses the conversational thread. The actual dialogue just vanishes and it starts fresh.",
            "runtime": {"response_delay_seconds": 14, "unresolved_turns": 2, "bug_retries": 1, "same_issue_mentions": 2},
        },
        "expected": {
            "labels_all": ["frustrated", "skeptical"],
            "queue_mode_in": ["steer"],
            "reply_style_in": ["repair_then_explain", "evidence_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "codex_compaction_false_timeline",
        "source": "https://github.com/openai/codex/issues/5957",
        "payload": {
            "message": "Compaction reset the session, you forgot the edits you just made, and then you confidently blamed previous sessions. Show me exactly what survived compaction before claiming anything.",
            "runtime": {"response_delay_seconds": 14, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2, "contradiction_signal": 0.44, "task_age_minutes": 65},
        },
        "expected": {
            "labels_all": ["frustrated", "skeptical"],
            "queue_mode_in": ["steer"],
            "reply_style_in": ["evidence_then_act", "repair_then_explain"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "openclaw_heartbeat_ignores_parameters",
        "source": "https://www.reddit.com/r/openclaw/comments/1s1s390/heartbeat_broken_i_used_cron_instead/",
        "payload": {
            "message": "The heartbeat simply does not execute, or it ignores parameters like isolatedSession and lightContext.",
            "runtime": {"response_delay_seconds": 15, "unresolved_turns": 3, "bug_retries": 2},
        },
        "expected": {
            "labels_all": ["frustrated", "skeptical"],
            "queue_mode_in": ["steer"],
            "reply_style_in": ["repair_then_explain", "evidence_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "claude_doubts_user_evidence",
        "source": "https://github.com/anthropics/claude-code/issues/10838",
        "payload": {
            "message": "I gave you a screenshot and clear evidence. Stop doubting the report and chasing imaginary causes. Inspect your own code and tell me the exact basis.",
            "runtime": {"response_delay_seconds": 11, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2, "contradiction_signal": 0.5},
        },
        "expected": {
            "labels_all": ["frustrated", "skeptical"],
            "queue_mode_in": ["steer"],
            "reply_style_in": ["evidence_then_act", "repair_then_explain"],
            "verification_in": ["very_high", "high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "openclaw_socket_zero_inbound_events",
        "source": "https://github.com/openclaw/openclaw/issues/45311",
        "payload": {
            "message": "Socket mode connected, then silence. No inbound events are ever logged, stale-socket restarts do nothing.",
            "runtime": {"response_delay_seconds": 16, "unresolved_turns": 3, "bug_retries": 2, "contradiction_signal": 0.34},
        },
        "expected": {
            "labels_all": ["frustrated", "skeptical"],
            "queue_mode_in": ["steer"],
            "reply_style_in": ["evidence_then_act", "repair_then_explain"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "openclaw_handoff_fallback_workspace",
        "source": "https://www.reddit.com/r/openclaw/comments/1rz9sr8/anyone_else_seeing_paperclip_openclaw_gateway/",
        "payload": {
            "message": "The handoff path is falling back to agent_home, projectId and workspaceId are null, and the context plumbing is lying to us. Stop guessing locally and check the handoff path.",
            "runtime": {"response_delay_seconds": 12, "unresolved_turns": 2, "contradiction_signal": 0.34},
        },
        "expected": {
            "labels_all": ["frustrated", "skeptical"],
            "queue_mode_in": ["steer"],
            "reply_style_in": ["evidence_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "hermes_forgets_rule_between_sessions",
        "source": "https://www.reddit.com/r/hermesagent/comments/1skesdm/hermes_agent_wont_remember_my_rules_how_are/",
        "payload": {
            "message": "This works within a session, but as soon as I start a new session, the agent completely forgets this rule.",
            "runtime": {"response_delay_seconds": 12, "unresolved_turns": 2, "same_issue_mentions": 2},
        },
        "expected": {
            "labels_all": ["frustrated", "skeptical"],
            "queue_mode_in": ["steer"],
            "reply_style_in": ["repair_then_explain", "evidence_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
    {
        "id": "hermes_hindsight_hangs_for_hours",
        "source": "https://www.reddit.com/r/hermesagent/comments/1sf4y9b/anyone_have_hindsight_working/",
        "payload": {
            "message": "Hindsight is available, but on the first prompt it just hangs installing packages for hours.",
            "runtime": {"response_delay_seconds": 22, "unresolved_turns": 3, "bug_retries": 1, "task_age_minutes": 180},
        },
        "expected": {
            "labels_all": ["frustrated"],
            "queue_mode_in": ["steer", "interrupt"],
            "reply_style_in": ["repair_then_explain"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 20,
        },
    },
] + long_tail.ABLATION_CASES


def baseline_plan() -> dict[str, object]:
    return {
        "mode": "neutral",
        "labels": ["neutral"],
        "queue_mode": "collect",
        "reply_style": "synthesize_then_recommend",
        "verification_level": "medium",
        "prefer_main_thread": False,
        "progress_update_interval_sec": 35,
    }


def skill_plan(payload: dict[str, object]) -> dict[str, object]:
    result = ee.run_pipeline(payload)
    return {
        "mode": result["confirmed_state"]["dominant_mode"],
        "labels": result["confirmed_state"]["labels"],
        "queue_mode": result["routing"]["thread_interface"]["queue_mode"],
        "reply_style": result["routing"]["reply_style"],
        "verification_level": result["routing"]["verification_level"],
        "prefer_main_thread": result["routing"]["thread_interface"]["prefer_main_thread"],
        "progress_update_interval_sec": result["routing"]["thread_interface"]["progress_update_interval_sec"],
    }


def score_plan(plan: dict[str, object], expected: dict[str, object]) -> tuple[int, int, dict[str, bool]]:
    checks: dict[str, bool] = {}
    mode_in = expected.get("mode_in") or expected.get("labels_all", [])
    if mode_in:
        checks["mode"] = str(plan["mode"]) in mode_in
    labels = set(plan["labels"])
    for label in expected.get("labels_all", []):
        checks[f"label:{label}"] = label in labels
    queue_mode_in = expected.get("queue_mode_in")
    if queue_mode_in:
        checks["queue_mode"] = str(plan["queue_mode"]) in queue_mode_in
    reply_style_in = expected.get("reply_style_in")
    if reply_style_in:
        checks["reply_style"] = str(plan["reply_style"]) in reply_style_in
    verification_in = expected.get("verification_in")
    if verification_in:
        checks["verification_level"] = str(plan["verification_level"]) in verification_in
    if "prefer_main_thread" in expected:
        checks["prefer_main_thread"] = bool(plan["prefer_main_thread"]) is bool(expected["prefer_main_thread"])
    if "max_progress_interval" in expected:
        checks["progress_update_interval_sec"] = int(plan["progress_update_interval_sec"]) <= int(expected["max_progress_interval"])
    passed = sum(1 for value in checks.values() if value)
    total = len(checks)
    return passed, total, checks


def main() -> int:
    rows = []
    skill_passed = 0
    skill_total = 0
    baseline_passed = 0
    baseline_total = 0
    for case in REAL_WORLD_CASES:
        skill = skill_plan(case["payload"])
        base = baseline_plan()
        skill_score, case_total, skill_checks = score_plan(skill, case["expected"])
        base_score, _, base_checks = score_plan(base, case["expected"])
        skill_passed += skill_score
        skill_total += case_total
        baseline_passed += base_score
        baseline_total += case_total
        rows.append(
            {
                "id": case["id"],
                "source": case["source"],
                "skill": {"score": skill_score, "total": case_total, "plan": skill, "checks": skill_checks},
                "baseline": {"score": base_score, "total": case_total, "plan": base, "checks": base_checks},
            }
        )
    summary = {
        "skill_passed": skill_passed,
        "skill_total": skill_total,
        "skill_rate": round(skill_passed / skill_total, 4) if skill_total else 0.0,
        "baseline_passed": baseline_passed,
        "baseline_total": baseline_total,
        "baseline_rate": round(baseline_passed / baseline_total, 4) if baseline_total else 0.0,
        "improvement": round((skill_passed / skill_total) - (baseline_passed / baseline_total), 4) if skill_total and baseline_total else 0.0,
        "results": rows,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
