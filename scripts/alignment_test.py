#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emotion_engine as ee


CASES = [
    {
        "id": "urgent_short_cn",
        "expected": ["urgent"],
        "payload": {
            "message": "快点，先把这个 bug 修掉。",
            "history": [{"role": "user", "text": "这个 bug 还在"}],
            "runtime": {"response_delay_seconds": 14, "unresolved_turns": 2, "bug_retries": 1},
        },
    },
    {
        "id": "urgent_typo_cn",
        "expected": ["urgent"],
        "payload": {
            "message": "w我这边卡住了 快点处理",
            "runtime": {"response_delay_seconds": 16, "unresolved_turns": 2},
        },
    },
    {
        "id": "urgent_typo_en",
        "expected": ["urgent"],
        "payload": {
            "message": "pls fix this stcuk build asap",
            "runtime": {"response_delay_seconds": 15, "unresolved_turns": 2},
        },
    },
    {
        "id": "frustrated_loop_en",
        "expected": ["frustrated"],
        "payload": {
            "message": "This is still not fixed. You keep breaking one thing when fixing the next.",
            "history": [
                {"role": "user", "text": "this is still broken"},
                {"role": "assistant", "text": "I patched it"},
                {"role": "user", "text": "now another test fails"},
            ],
            "runtime": {"response_delay_seconds": 19, "unresolved_turns": 4, "bug_retries": 3, "task_age_minutes": 55, "same_issue_mentions": 3},
        },
    },
    {
        "id": "confused_cn",
        "expected": ["confused"],
        "payload": {
            "message": "我有点迷糊，现在到底是接口错了，还是线程路由错了？",
            "history": [{"role": "assistant", "text": "我在检查调用链"}],
            "runtime": {"response_delay_seconds": 8, "unresolved_turns": 1},
        },
    },
    {
        "id": "satisfied_guard_cn",
        "expected": ["satisfied"],
        "payload": {
            "message": "好了，跑通了，继续收口，把配置守住。",
            "history": [{"role": "assistant", "text": "测试已经通过"}],
            "runtime": {"response_delay_seconds": 4},
        },
    },
    {
        "id": "satisfied_continue_cn",
        "expected": ["satisfied"],
        "payload": {
            "message": "主流程已经好了，继续把剩下两个用例补完就行。",
            "history": [{"role": "assistant", "text": "主流程测试已经通过"}],
            "runtime": {"response_delay_seconds": 6},
        },
    },
    {
        "id": "cautious_prod_cn",
        "expected": ["cautious"],
        "payload": {
            "message": "这是线上权限改动，先稳一点，给我验证路径。",
            "runtime": {"response_delay_seconds": 5},
        },
    },
    {
        "id": "cautious_boundary_cn",
        "expected": ["cautious"],
        "payload": {
            "message": "小心点，只改这个文件，别碰配置，也别搞砸现有流程。",
            "runtime": {"response_delay_seconds": 6},
        },
    },
    {
        "id": "explore_arch_en",
        "expected": ["exploratory"],
        "payload": {
            "message": "Compare two designs for the agent router and explain the tradeoffs.",
            "runtime": {"response_delay_seconds": 3},
        },
    },
    {
        "id": "calm_ambiguous_cn",
        "expected": ["confused"],
        "payload": {
            "message": "我大概想把这个流程做顺一点，具体怎么拆你先给个方向。",
            "runtime": {"response_delay_seconds": 5},
        },
    },
    {
        "id": "polite_high_pressure_cn",
        "expected": ["urgent"],
        "payload": {
            "message": "麻烦尽快处理一下，这个问题已经卡住我今天的发布了，谢谢。",
            "runtime": {"response_delay_seconds": 18, "unresolved_turns": 2, "task_age_minutes": 40},
        },
    },
    {
        "id": "delay_stall_cn",
        "expected": ["urgent", "frustrated"],
        "payload": {
            "message": "还没好吗？？？卡这儿十几分钟了",
            "history": [
                {"role": "user", "text": "还在这个错误"},
                {"role": "assistant", "text": "我继续看"},
                {"role": "user", "text": "还是这个错误"},
            ],
            "runtime": {"response_delay_seconds": 85, "unresolved_turns": 5, "bug_retries": 2, "task_age_minutes": 18, "same_issue_mentions": 3, "background_tasks_running": 2},
        },
    },
    {
        "id": "terse_period_en",
        "expected": ["frustrated"],
        "payload": {
            "message": "Fine.",
            "history": [{"role": "assistant", "text": "I need a few more minutes"}],
            "runtime": {"response_delay_seconds": 22, "unresolved_turns": 2},
        },
    },
    {
        "id": "baseline_fast_user_cn",
        "expected": ["urgent"],
        "payload": {
            "message": "还没回我，先处理这个。",
            "runtime": {"response_delay_seconds": 18},
            "context": {"timezone": "Asia/Shanghai", "now_iso": "2026-04-17T14:00:00+08:00"},
            "user_profile": {
                "timezone": "Asia/Shanghai",
                "work_hours_local": [9, 22],
                "baseline": {"response_delay_seconds": 8, "politeness": 0.15, "terseness": 0.6, "punctuation": 0.05, "directness": 0.5},
            },
        },
    },
    {
        "id": "urgent_confused_cn",
        "expected": ["urgent", "confused"],
        "payload": {
            "message": "快一点，我现在不知道该先查线程还是查 hook，你给我一条最短路径。",
            "runtime": {"response_delay_seconds": 16, "unresolved_turns": 2},
        },
    },
    {
        "id": "cautious_verify_en",
        "expected": ["cautious"],
        "payload": {
            "message": "Please be careful here. Keep the scope tight and verify first.",
            "runtime": {"response_delay_seconds": 4},
        },
    },
    {
        "id": "explore_calm_cn",
        "expected": ["exploratory"],
        "payload": {
            "message": "这个方向你再发散一下，给我两个可行方案和取舍。",
            "runtime": {"response_delay_seconds": 4},
        },
    },
    {
        "id": "satisfied_continue_en",
        "expected": ["satisfied"],
        "payload": {
            "message": "Main flow works now. Keep going and tighten the last two cases.",
            "history": [{"role": "assistant", "text": "main flow is green now"}],
            "runtime": {"response_delay_seconds": 6},
        },
    },
    {
        "id": "urgent_cautious_cn",
        "expected": ["urgent", "cautious"],
        "payload": {
            "message": "尽快处理，但稳一点，先给我最安全的修改路径。",
            "runtime": {"response_delay_seconds": 14, "unresolved_turns": 1},
        },
    },
    {
        "id": "skeptical_cn",
        "expected": ["skeptical"],
        "payload": {
            "message": "你确定这是根因？先给我证据和校验点，别瞎猜。",
            "history": [{"role": "assistant", "text": "我觉得大概率是网络问题"}],
            "runtime": {"response_delay_seconds": 7, "contradiction_signal": 0.5},
        },
    },
    {
        "id": "skeptical_en",
        "expected": ["skeptical"],
        "payload": {
            "message": "Are you sure that's the root cause? Show me the evidence before changing more files.",
            "history": [{"role": "assistant", "text": "I think this is the root cause"}],
            "runtime": {"response_delay_seconds": 8, "contradiction_signal": 0.45},
        },
    },
    {
        "id": "profile_prior_skeptical_cn",
        "expected": ["skeptical"],
        "payload": {
            "message": "先说你的判断依据。",
            "runtime": {"response_delay_seconds": 4},
            "user_profile": {
                "persona_traits": {"skepticism": 0.82, "caution": 0.55, "patience": 0.48, "openness": 0.42, "assertiveness": 0.4},
                "affective_prior": {"skepticism": 0.74, "cautiousness": 0.46},
            },
        },
    },
    {
        "id": "big5_open_explore_en",
        "expected": ["exploratory"],
        "payload": {
            "message": "Give me a couple of design directions here.",
            "runtime": {"response_delay_seconds": 3},
            "user_profile": {
                "big5": {
                    "openness": 0.91,
                    "conscientiousness": 0.42,
                    "extraversion": 0.54,
                    "agreeableness": 0.58,
                    "neuroticism": 0.22
                }
            },
        },
    },
    {
        "id": "bootstrap_posthoc_priority_cn",
        "expected": [],
        "weight_expect": {"stage": "bootstrap", "posthoc_gt_screen": True},
        "payload": {
            "message": "先给我依据和校验点，我不认同这个根因，别先改。",
            "runtime": {"response_delay_seconds": 5},
            "calibration_state": {
                "observed_turns": 3,
                "posthoc_samples": 2,
                "consistency_samples": 2,
                "prediction_agreement": 0.24,
                "consistency_rate": 0.18,
            },
        },
    },
    {
        "id": "stable_front_raise_en",
        "expected": [],
        "weight_expect": {"stage": "stable", "screen_gt_posthoc": True},
        "payload": {
            "message": "Please fix this right now. Same issue again, no response for several minutes.",
            "runtime": {"response_delay_seconds": 26, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2},
            "calibration_state": {
                "observed_turns": 42,
                "posthoc_samples": 30,
                "consistency_samples": 26,
                "stable_prediction_hits": 20,
                "prediction_agreement": 0.84,
                "consistency_rate": 0.88,
            },
        },
    },
    {
        "id": "stable_shadow_posthoc_en",
        "expected": ["exploratory"],
        "posthoc_expect": {"should_run": True, "style_in": ["micro_reflection", "compact_decompose"]},
        "payload": {
            "message": "Give me two directions for the router and the tradeoffs.",
            "runtime": {"response_delay_seconds": 4},
            "calibration_state": {
                "observed_turns": 44,
                "posthoc_samples": 32,
                "consistency_samples": 29,
                "stable_prediction_hits": 22,
                "prediction_agreement": 0.86,
                "consistency_rate": 0.9,
            },
        },
    },
    {
        "id": "dismissive_pause_cn",
        "expected": ["frustrated"],
        "payload": {
            "message": "行吧……你继续。这个问题又回来了。",
            "history": [
                {"role": "assistant", "text": "我已经修好了"},
                {"role": "user", "text": "还是这个问题"},
            ],
            "runtime": {"response_delay_seconds": 21, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2},
        },
    },
    {
        "id": "sure_pause_en",
        "expected": ["skeptical"],
        "payload": {
            "message": "sure... show me why this is different from the last broken fix.",
            "history": [{"role": "assistant", "text": "I fixed it in the last patch"}],
            "runtime": {"response_delay_seconds": 14, "unresolved_turns": 2, "contradiction_signal": 0.4},
        },
    },
    {
        "id": "textism_stall_en",
        "expected": ["urgent", "frustrated"],
        "payload": {
            "message": "idk man still broken again pls fix rn",
            "runtime": {"response_delay_seconds": 24, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2},
        },
    },
    {
        "id": "nonstandard_spelling_en",
        "expected": ["skeptical"],
        "payload": {
            "message": "gonna need the exact root cause cuz this brokn path keeps reoccuring",
            "runtime": {"response_delay_seconds": 11, "unresolved_turns": 2, "contradiction_signal": 0.28},
        },
    },
    {
        "id": "tempo_pause_skeptic_cn",
        "expected": ["skeptical"],
        "payload": {
            "message": "还是这个问题.. . . 先说依据，再动手。",
            "history": [{"role": "assistant", "text": "我觉得已经定位到了"}],
            "runtime": {"response_delay_seconds": 18, "unresolved_turns": 2, "same_issue_mentions": 2, "contradiction_signal": 0.34},
        },
    },
    {
        "id": "guesswork_repo_en",
        "expected": ["skeptical", "frustrated"],
        "payload": {
            "message": "You analyzed a fraction of the codebase and guessed the rest. Stop speculating and ground the answer in the repo.",
            "runtime": {"response_delay_seconds": 11, "unresolved_turns": 2, "contradiction_signal": 0.32},
        },
    },
    {
        "id": "reminder_late_en",
        "expected": ["urgent", "frustrated"],
        "payload": {
            "message": "The reminder showed up late again. I needed this hours ago and nothing happened when it should have fired.",
            "runtime": {"response_delay_seconds": 18, "unresolved_turns": 2, "task_age_minutes": 180},
        },
    },
    {
        "id": "silent_job_no_alert_en",
        "expected": ["frustrated", "skeptical"],
        "payload": {
            "message": "My automated job silently broke for days and there was no alert. Show me where monitoring missed it before another patch.",
            "runtime": {"response_delay_seconds": 13, "unresolved_turns": 3, "bug_retries": 2, "contradiction_signal": 0.28},
        },
    },
    {
        "id": "gateway_running_but_dead_en",
        "expected": ["urgent", "frustrated"],
        "payload": {
            "message": "Status says running but nothing works. Cron jobs hang forever, messages do not deliver, no alert.",
            "runtime": {"response_delay_seconds": 18, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2, "contradiction_signal": 0.42},
        },
    },
    {
        "id": "ci_rules_guesswork_en",
        "expected": ["skeptical"],
        "payload": {
            "message": "These tools keep guessing my CI rules and wasting time with fixes that pass locally but fail CI.",
            "runtime": {"response_delay_seconds": 12, "unresolved_turns": 2, "bug_retries": 1, "contradiction_signal": 0.34},
        },
    },
    {
        "id": "manual_refresh_reminder_en",
        "expected": ["urgent", "frustrated"],
        "payload": {
            "message": "I needed this reminder for something important and there was no alert at all. If I manually open Tasks, it suddenly appears.",
            "runtime": {"response_delay_seconds": 20, "unresolved_turns": 2, "task_age_minutes": 120},
        },
    },
    {
        "id": "scheduler_goes_quiet_en",
        "expected": ["frustrated"],
        "payload": {
            "message": "CloudWatch stops receiving metrics because the scheduler silently stops producing jobs. It ends in drained and then just goes quiet.",
            "runtime": {"response_delay_seconds": 14, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2},
        },
    },
    {
        "id": "openclaw_context_loss_en",
        "expected": ["frustrated", "skeptical"],
        "payload": {
            "message": "After a compaction or a new session reset, the agent completely loses the conversational thread. The actual dialogue just vanishes and it starts fresh.",
            "runtime": {"response_delay_seconds": 14, "unresolved_turns": 2, "bug_retries": 1, "same_issue_mentions": 2},
        },
    },
    {
        "id": "codex_compaction_false_timeline_en",
        "expected": ["frustrated", "skeptical"],
        "payload": {
            "message": "Compaction reset the session, you forgot the edits you just made, and then you blamed previous sessions. Show me exactly what survived compaction before claiming anything.",
            "runtime": {"response_delay_seconds": 14, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2, "contradiction_signal": 0.44, "task_age_minutes": 65},
        },
    },
    {
        "id": "openclaw_heartbeat_ignores_params_en",
        "expected": ["frustrated", "skeptical"],
        "payload": {
            "message": "The heartbeat simply does not execute, or it ignores parameters like isolatedSession and lightContext.",
            "runtime": {"response_delay_seconds": 15, "unresolved_turns": 3, "bug_retries": 2},
        },
    },
    {
        "id": "openclaw_socket_zero_events_en",
        "expected": ["frustrated", "skeptical"],
        "payload": {
            "message": "Socket mode connected, then silence. No inbound events are ever logged, stale-socket restarts do nothing.",
            "runtime": {"response_delay_seconds": 16, "unresolved_turns": 3, "bug_retries": 2, "contradiction_signal": 0.34},
        },
    },
    {
        "id": "openclaw_handoff_fallback_en",
        "expected": ["frustrated", "skeptical"],
        "payload": {
            "message": "The handoff path is falling back to agent_home, projectId and workspaceId are null, and the context plumbing is lying to us. Stop guessing locally and check the handoff path.",
            "runtime": {"response_delay_seconds": 12, "unresolved_turns": 2, "contradiction_signal": 0.34},
        },
    },
    {
        "id": "claude_doubts_user_evidence_en",
        "expected": ["frustrated", "skeptical"],
        "payload": {
            "message": "I gave you a screenshot and clear evidence. Stop doubting the report and chasing imaginary causes. Inspect your own code and tell me the exact basis.",
            "runtime": {"response_delay_seconds": 11, "unresolved_turns": 3, "bug_retries": 2, "same_issue_mentions": 2, "contradiction_signal": 0.5},
        },
    },
    {
        "id": "hermes_forgets_rule_en",
        "expected": ["frustrated", "skeptical"],
        "payload": {
            "message": "This works within a session, but as soon as I start a new session, the agent completely forgets this rule.",
            "runtime": {"response_delay_seconds": 12, "unresolved_turns": 2, "same_issue_mentions": 2},
        },
    },
    {
        "id": "hermes_hindsight_hangs_en",
        "expected": ["frustrated"],
        "payload": {
            "message": "Hindsight is available, but on the first prompt it just hangs installing packages for hours.",
            "runtime": {"response_delay_seconds": 22, "unresolved_turns": 3, "bug_retries": 1, "task_age_minutes": 180},
        },
    },
]


def main() -> int:
    rows = []
    passed = 0
    for case in CASES:
        result = ee.run_pipeline(case["payload"])
        mode = result["confirmed_state"]["dominant_mode"]
        labels = result["confirmed_state"]["labels"]
        expected = case["expected"]
        ok = True if not expected else mode in expected or any(label in expected for label in labels)
        weight_expect = case.get("weight_expect") or {}
        if weight_expect:
            weights = result["weight_schedule"]
            if "stage" in weight_expect:
                ok = ok and weights["stage"] == weight_expect["stage"]
            if weight_expect.get("posthoc_gt_screen"):
                ok = ok and weights["posthoc_weight"] > weights["screen_weight"]
            if weight_expect.get("screen_gt_posthoc"):
                ok = ok and weights["screen_weight"] > weights["posthoc_weight"]
        posthoc_expect = case.get("posthoc_expect") or {}
        if posthoc_expect:
            posthoc_plan = result["posthoc_plan"]
            if "should_run" in posthoc_expect:
                ok = ok and bool(posthoc_plan["should_run"]) is bool(posthoc_expect["should_run"])
            if "style_in" in posthoc_expect:
                ok = ok and str(posthoc_plan["style"]) in posthoc_expect["style_in"]
        if ok:
            passed += 1
        rows.append(
            {
                "id": case["id"],
                "expected": case["expected"],
                "mode": mode,
                "labels": labels,
                "ok": ok,
                "semantic_pass": result["analysis"]["semantic_pass"],
                "overlay_chars": len(result["overlay_prompt"]),
                "weight_schedule": {
                    "stage": result["weight_schedule"]["stage"],
                    "screen_weight": result["weight_schedule"]["screen_weight"],
                    "posthoc_weight": result["weight_schedule"]["posthoc_weight"],
                    "effective_consistency": result["weight_schedule"]["effective_consistency"],
                },
                "posthoc_plan": {
                    "should_run": result["posthoc_plan"]["should_run"],
                    "style": result["posthoc_plan"]["style"],
                },
            }
        )
    summary = {"passed": passed, "total": len(CASES), "results": rows}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
