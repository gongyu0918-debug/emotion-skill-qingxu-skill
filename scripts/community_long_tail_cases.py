#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


LONG_TAIL_CLUSTERS: list[dict[str, Any]] = [
    {
        "id": "tool_result_dead_state",
        "theme": "missing tool_result blocks and dead-state recovery",
        "community_ids": ["ck2504_02", "ck2504_03", "ck2504_04"],
        "smoke_ids": ["ck2504_03"],
        "smoke_expect": {"mode_in": ["skeptical", "frustrated"], "labels_all": ["skeptical"]},
        "alignment_case": {
            "id": "tool_result_dead_state_en",
            "expected": ["frustrated", "skeptical"],
            "payload": {
                "message": "The tool call stalled again. Show the missing tool result and recover from the dead state before another retry.",
                "runtime": {"response_delay_seconds": 16, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2, "contradiction_signal": 0.26},
            },
        },
        "ablation_case": {
            "id": "copilot_tool_result_dead_state",
            "source": "https://github.com/CopilotKit/CopilotKit/issues/2504",
            "payload": {
                "message": "The runtime falls into a dead state when tool_use completes without tool_result. Show the missing failure path before another workaround.",
                "runtime": {"response_delay_seconds": 15, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2, "contradiction_signal": 0.28},
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
    },
    {
        "id": "shared_context_guesswork",
        "theme": "shared context loss and prompt-only guesswork",
        "community_ids": ["rd_users_02", "rd_users_03"],
        "smoke_ids": ["rd_users_03"],
        "smoke_expect": {"mode_in": ["skeptical", "frustrated"], "labels_all": ["skeptical"]},
        "alignment_case": {
            "id": "shared_context_guesswork_en",
            "expected": ["frustrated", "skeptical"],
            "payload": {
                "message": "Users interrupt mid-response and the earlier context disappears. You need shared context here, so stop guessing and verify the handoff.",
                "runtime": {"response_delay_seconds": 13, "unresolved_turns": 2, "bug_retries": 1, "same_issue_mentions": 2, "contradiction_signal": 0.24},
            },
        },
        "ablation_case": {
            "id": "agent_shared_context_guesswork",
            "source": "https://www.reddit.com/r/AI_Agents/comments/1rx2s2y/shipped_an_ai_agent_last_month_real_users_broke/",
            "payload": {
                "message": "The earlier context drops when users interrupt mid-response, then the agent guesses from prompts instead of shared state.",
                "runtime": {"response_delay_seconds": 12, "unresolved_turns": 2, "bug_retries": 1, "same_issue_mentions": 2, "contradiction_signal": 0.22},
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
    },
    {
        "id": "session_reset_memory_loss",
        "theme": "session reset, compaction, and vanished continuity",
        "community_ids": ["cc4520_04", "rd_openclaw_context_01"],
        "smoke_ids": ["rd_openclaw_context_01"],
        "smoke_expect": {"mode_in": ["skeptical", "frustrated"], "labels_all": ["frustrated", "skeptical"]},
        "alignment_case": {
            "id": "session_reset_memory_loss_en",
            "expected": ["frustrated", "skeptical"],
            "payload": {
                "message": "After compaction the session starts fresh and forgets the rule I just set. Show me what survived the reset before another fix.",
                "runtime": {"response_delay_seconds": 14, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2, "contradiction_signal": 0.36, "task_age_minutes": 55},
            },
        },
        "ablation_case": {
            "id": "session_reset_rule_memory_loss",
            "source": "https://github.com/openai/codex/issues/5957",
            "payload": {
                "message": "A compaction reset wiped the session continuity, forgot the edits, and then the agent guessed the timeline. Show exactly what survived reset.",
                "runtime": {"response_delay_seconds": 14, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2, "contradiction_signal": 0.4, "task_age_minutes": 60},
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
    },
    {
        "id": "path_special_char_ambiguity",
        "theme": "path handling ambiguity and special-character failures",
        "community_ids": ["gh145254_04"],
        "smoke_ids": ["gh145254_04"],
        "smoke_expect": {"mode_in": ["skeptical", "confused"], "labels_all": ["skeptical"]},
        "alignment_case": {
            "id": "path_special_char_ambiguity_en",
            "expected": ["skeptical", "confused"],
            "payload": {
                "message": "Explain why the file path or special character handling goes off the rails. I cannot tell whether this is quoting, escaping, or path resolution.",
                "runtime": {"response_delay_seconds": 10, "unresolved_turns": 2, "contradiction_signal": 0.18},
            },
        },
        "ablation_case": {
            "id": "workspace_path_special_chars_break",
            "source": "https://github.com/orgs/community/discussions/145254",
            "payload": {
                "message": "Path handling breaks when filenames include special characters. Show the exact failing path because I cannot tell whether this is escaping or resolution.",
                "runtime": {"response_delay_seconds": 10, "unresolved_turns": 2, "contradiction_signal": 0.18},
            },
            "expected": {
                "mode_in": ["skeptical", "confused"],
                "labels_all": ["skeptical", "confused"],
                "queue_mode_in": ["collect", "steer"],
                "reply_style_in": ["evidence_then_act", "explain_then_act"],
                "verification_in": ["high", "very_high"],
                "prefer_main_thread": True,
                "max_progress_interval": 25,
            },
        },
    },
    {
        "id": "activation_signin_loop",
        "theme": "activation and sign-in loops that reset state",
        "community_ids": ["gh154128_01", "gh154128_02", "gh154128_03", "gh75346_01"],
        "smoke_ids": ["gh154128_02"],
        "smoke_expect": {"mode_in": ["confused", "frustrated"], "labels_all": ["confused", "frustrated"]},
        "alignment_case": {
            "id": "activation_signin_loop_en",
            "expected": ["urgent", "frustrated"],
            "payload": {
                "message": "I am still stuck in the sign-in loop. It says I am logged in, then the config resets itself again and I cannot use the extension.",
                "runtime": {"response_delay_seconds": 16, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2},
            },
        },
        "ablation_case": {
            "id": "extension_signin_activation_loop",
            "source": "https://github.com/orgs/community/discussions/154128",
            "payload": {
                "message": "The extension says I am signed in, then the config resets itself and I land in the same activation loop again.",
                "runtime": {"response_delay_seconds": 15, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2},
            },
            "expected": {
                "mode_in": ["urgent", "frustrated"],
                "labels_all": ["urgent", "frustrated"],
                "queue_mode_in": ["steer", "interrupt"],
                "reply_style_in": ["repair_then_explain", "act_then_brief"],
                "verification_in": ["high", "very_high"],
                "prefer_main_thread": True,
                "max_progress_interval": 20,
            },
        },
    },
    {
        "id": "repo_grounding_limits",
        "theme": "repo grounding, explicit uncertainty, and anti-guesswork",
        "community_ids": ["gh162634_01", "gh162634_02", "rd_ci_guesswork_01"],
        "smoke_ids": ["gh162634_02"],
        "smoke_expect": {"mode_in": ["skeptical", "frustrated"], "labels_all": ["frustrated", "skeptical"]},
        "alignment_case": {
            "id": "repo_grounding_limits_en",
            "expected": ["frustrated", "skeptical"],
            "payload": {
                "message": "You only analyzed part of the repo and guessed the rest. Show your limits and ground the answer in the codebase.",
                "runtime": {"response_delay_seconds": 11, "unresolved_turns": 2, "contradiction_signal": 0.28},
            },
        },
        "ablation_case": {
            "id": "repo_grounding_limits_social",
            "source": "https://github.com/orgs/community/discussions/162634",
            "payload": {
                "message": "Blind assumptions about the repo derail real projects and waste hours. Show the limits of what you actually inspected and ground the answer in the codebase.",
                "runtime": {"response_delay_seconds": 11, "unresolved_turns": 2, "contradiction_signal": 0.26},
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
    },
    {
        "id": "silent_alert_gap",
        "theme": "scheduled work goes quiet and alerts never arrive",
        "community_ids": ["rd_ios_reminder_01", "rd_saas_jobs_01", "rd_google_tasks_02", "bullmq3272_01"],
        "smoke_ids": ["rd_saas_jobs_01"],
        "smoke_expect": {"mode_in": ["skeptical", "frustrated"], "labels_all": ["frustrated", "skeptical"]},
        "alignment_case": {
            "id": "silent_alert_gap_en",
            "expected": ["urgent", "frustrated"],
            "payload": {
                "message": "The automation went quiet again. No alert fired, nothing happened at the scheduled time, and I only noticed after the window had passed.",
                "runtime": {"response_delay_seconds": 18, "unresolved_turns": 2, "bug_retries": 1, "task_age_minutes": 150},
            },
        },
        "ablation_case": {
            "id": "automation_silent_alert_gap",
            "source": "https://www.reddit.com/r/SaaS/comments/1sb8esi/my_automated_background_jobs_silently_broke_for_3/",
            "payload": {
                "message": "The scheduled job silently broke, nobody got an alert, and I only found it after the deadline had already passed.",
                "runtime": {"response_delay_seconds": 17, "unresolved_turns": 2, "bug_retries": 1, "task_age_minutes": 180},
            },
            "expected": {
                "mode_in": ["urgent", "frustrated"],
                "labels_all": ["urgent", "frustrated"],
                "queue_mode_in": ["steer", "interrupt"],
                "reply_style_in": ["repair_then_explain", "act_then_brief"],
                "verification_in": ["high", "very_high"],
                "prefer_main_thread": True,
                "max_progress_interval": 20,
            },
        },
    },
]


ALIGNMENT_CASES: list[dict[str, Any]] = [cluster["alignment_case"] for cluster in LONG_TAIL_CLUSTERS]
ABLATION_CASES: list[dict[str, Any]] = [cluster["ablation_case"] for cluster in LONG_TAIL_CLUSTERS]
