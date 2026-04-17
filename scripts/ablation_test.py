#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
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
            "labels_all": ["urgent", "frustrated"],
            "queue_mode_in": ["steer", "interrupt"],
            "reply_style_in": ["act_then_brief", "repair_then_explain"],
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
            "labels_all": ["skeptical", "cautious"],
            "queue_mode_in": ["collect", "steer"],
            "reply_style_in": ["evidence_then_act", "verify_then_act"],
            "verification_in": ["high", "very_high"],
            "prefer_main_thread": True,
            "max_progress_interval": 25,
        },
    },
]


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
