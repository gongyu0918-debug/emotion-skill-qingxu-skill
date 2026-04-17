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
            }
        )
    summary = {"passed": passed, "total": len(CASES), "results": rows}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
