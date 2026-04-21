---
name: emotion-skill
description: Emotion-aware orchestration for coding agents. Detect urgency, frustration, skepticism, confusion, caution, satisfaction, and openness from coding-task wording, retries, delay pressure, and dialogue history, then route verification depth, queue priority, reply style, and stabilization strategy. Use when: coding agent orchestration, repo debugging, scope protection, verification depth control, and post-success stabilization.
license: MIT
metadata:
  openclaw:
    emoji: "🎛️"
    os: ["darwin", "linux", "win32"]
---

# 情绪.skill / Emotion Skill

让 Agent 听懂空气，不只是听懂任务。

Teach an agent to read the room, not just the task.

这个 skill 做的事情很简单：

- 用户开始急了，它少铺垫，先动手
- 用户开始怀疑，它先拿依据再开工
- 用户很谨慎，它把 scope 收紧
- 用户已经满意，它别继续乱改，直接收口

What this skill does:

- when the user turns urgent, it cuts the padding and acts first
- when the user turns skeptical, it shows the basis before making moves
- when the user turns cautious, it tightens scope
- when the user is already satisfied, it stops pushing and switches to closing mode

它是一个编排层，负责把用户状态翻译成执行策略。

It is an orchestration layer that turns user state into execution policy.

它盯着一轮对话里那些细小但真实的东西：

- 词汇的硬度
- 标点的密度
- 错别字和赶打感
- 同一个问题反复出现
- 长时间没响应后的语气变化
- 那种用户自己都没留意到的轻微修正，比如 `不一定`

It watches the small but real signals inside a turn:

- how hard the wording feels
- how dense the punctuation gets
- typos and rushed typing
- the same issue showing up again
- tone shifts after long silence
- tiny corrections the user may not even notice, such as `not necessarily`

然后把这些信号翻译成 Agent 的工作模式。

Then it turns those signals into execution policy.

## Scope And Non-Goals

这个 skill 的目标很窄：

- coding agent 对话编排
- repo 调试和修复过程里的情绪状态识别
- scope、验证强度、线程优先级、收口策略调整

This skill has a narrow scope:

- coding-agent orchestration
- emotion-state detection during repo debugging and repair work
- scope control, verification depth, thread priority, and guard-mode shifts

市场文案要始终保持在开发者工作流这条线上：

- repository debugging
- agent runtime routing
- verification depth control
- thread and heartbeat coordination
- stabilization after success

Marketplace copy should stay anchored to developer workflows:

- repository debugging
- agent runtime routing
- verification depth control
- thread and heartbeat coordination
- stabilization after success

## Language Coverage

当前特化校准只覆盖两种语言：

- 中文
- 英文

The current specialized calibration covers two languages:

- Chinese
- English

这两条线有单独整理过的共性情绪表达、社区语料、标点习惯、节奏停顿、赶打错拼和 agent-coding 抱怨模式。

These two tracks have explicit calibration for shared emotion cues, community phrasing, punctuation habits, rhythmic pauses, rushed typos, and agent-coding complaint patterns.

其他语言目前只有弱支持：

- 通用标点强度
- 重复和停顿
- 延迟压力
- 多轮重复失败
- 命令语气和结构性线索

Other languages currently receive only light support:

- generic punctuation intensity
- repetition and pause rhythm
- delay pressure
- repeated failure across turns
- imperative tone and structural cues

发布说明里应该明确写这一点：当前版本没有对其他语言做专门特化训练或独立语料校准。

The release notes should say this plainly: the current version does not include language-specific tuning or dedicated calibration corpora for languages beyond Chinese and English.

采集层一直是四路并行：

- 前置情绪标签 prompt
- 后置反问 prompt
- 历史上下文
- 时间戳、延迟、重试和卡住状态

The collection layer always runs four signals in parallel:

- front emotion-label prompt
- review-pass prompt
- dialogue history
- timestamp, delay, retry, and stall state

## Quick Start

先跑一轮，把当前用户消息丢进引擎里看看它怎么读空气：

```bash
python scripts/emotion_engine.py run --message "先给我依据，别瞎猜" --pretty
```

Start with one run. Feed the latest turn in and see how the engine reads the room:

```bash
python scripts/emotion_engine.py run --message "Show me the basis before changing more files." --pretty
```

再跑一个更真实的 demo payload：

```bash
python scripts/emotion_engine.py run --input demo/local_history_event.json --pretty
```

Run the bundled local-history demo payload:

```bash
python scripts/emotion_engine.py run --input demo/local_history_event.json --pretty
```

如果你要补一个最小宿主适配层，直接跑：

```bash
python scripts/minimal_host_adapter.py --event demo/local_history_event.json --store-dir .demo-store --pretty
```

For a minimal host-side profile adapter, run:

```bash
python scripts/minimal_host_adapter.py --event demo/local_history_event.json --store-dir .demo-store --pretty
```

然后按这个顺序接进去：

1. 把 `overlay_prompt` 塞进当前这一轮，当成一个很小的动态前置提示。
2. 把 `routing.thread_interface` 接到队列、线程、heartbeat 和子任务路由。
3. 如果 `guidance.hook_mode` 是 `latent`，先用 `guidance.soft_probe_seed`。只有真的值得打断用户时，再用 `guidance.question`。
4. 先看 `analysis.semantic_pass`。它是 `fast` 的时候，再去跑模型语义复核。
5. 如果你想让模型也参与判断，去看 `references/model-prompts.md`，把结果按 `llm_semantic` 回填。
6. 看状态时别只盯一个标签，要一起看 `confirmed_state.emotion_vector` 和 `mode_scores`。情绪可以并存，`dominant_mode` 只负责决定这轮谁来主导编排。
7. 冷启动阶段建议让 review pass 跟随每轮一起运行；一致性升高后，把它压缩成一个很短的 shadow review。
8. 等 `calibration_state.consistency_rate` 和 `consistency_samples` 长起来，再慢慢抬高前置权重。

Then wire it in like this:

1. Drop `overlay_prompt` into the current turn as a small dynamic pre-prompt.
2. Feed `routing.thread_interface` into queueing, thread priority, heartbeat, and subagent routing.
3. If `guidance.hook_mode` is `latent`, start with `guidance.soft_probe_seed`. Reach for `guidance.question` only when the interruption is worth it.
4. Check `analysis.semantic_pass` first. Only run the semantic model pass when it says `fast`.
5. If you want model-side judgment, read `references/model-prompts.md` and feed the result back as `llm_semantic`.
6. Do not stare at one label in isolation. Read `confirmed_state.emotion_vector` and `mode_scores` together. Emotions can coexist. `dominant_mode` only decides who drives the turn.
7. During cold start, keep the review pass available on each turn. As consistency rises, compress it into a short shadow review.
8. Raise front weight only after `calibration_state.consistency_rate` and `consistency_samples` become believable.

## Input Contract

Pass a JSON object with any of these fields:

```json
{
  "message": "latest user message",
  "context": {
    "timezone": "Asia/Shanghai",
    "now_iso": "2026-04-17T14:20:00+08:00"
  },
  "history": [
    {"role": "user", "text": "earlier user turn"},
    {"role": "assistant", "text": "earlier assistant turn"}
  ],
  "user_profile": {
    "id": "user-123",
    "timezone": "Asia/Shanghai",
    "work_hours_local": [9, 22],
    "persona_traits": {
      "patience": 0.55,
      "skepticism": 0.48,
      "caution": 0.52,
      "openness": 0.44,
      "assertiveness": 0.38
    },
    "big5": {
      "openness": 0.7,
      "conscientiousness": 0.62,
      "extraversion": 0.41,
      "agreeableness": 0.56,
      "neuroticism": 0.36
    },
    "affective_prior": {
      "urgency": 0.12,
      "frustration": 0.1,
      "confusion": 0.08,
      "skepticism": 0.42,
      "satisfaction": 0.12,
      "cautiousness": 0.28,
      "openness": 0.2
    },
    "baseline": {
      "response_delay_seconds": 35,
      "politeness": 0.2,
      "terseness": 0.35,
      "punctuation": 0.15,
      "directness": 0.3
    }
  },
  "runtime": {
    "response_delay_seconds": 18,
    "unresolved_turns": 4,
    "bug_retries": 2,
    "task_age_minutes": 25,
    "queue_depth": 1,
    "background_tasks_running": 2,
    "same_issue_mentions": 2
  },
  "last_state": {
    "vector": {
      "urgency": 0.4,
      "frustration": 0.2,
      "clarity": 0.6,
      "satisfaction": 0.1,
      "trust": 0.5,
      "engagement": 0.7
    },
    "emotion_vector": {
      "urgency": 0.4,
      "frustration": 0.2,
      "confusion": 0.3,
      "skepticism": 0.35,
      "satisfaction": 0.1,
      "cautiousness": 0.2,
      "openness": 0.5
    },
    "ttl_seconds": 1200
  },
  "calibration_state": {
    "observed_turns": 18,
    "posthoc_samples": 11,
    "consistency_samples": 9,
    "stable_prediction_hits": 6,
    "prediction_agreement": 0.58,
    "consistency_rate": 0.63
  },
  "llm_semantic": {
    "labels": ["urgent", "frustrated"],
    "confidence": 0.78,
    "emotion_vector": {
      "urgency": 0.88,
      "frustration": 0.82,
      "confusion": 0.41,
      "skepticism": 0.28,
      "satisfaction": 0.08,
      "cautiousness": 0.12,
      "openness": 0.2
    }
  },
  "posthoc_semantic": {
    "labels": ["skeptical"],
    "confidence": 0.71,
    "emotion_vector": {
      "urgency": 0.14,
      "frustration": 0.18,
      "confusion": 0.12,
      "skepticism": 0.58,
      "satisfaction": 0.05,
      "cautiousness": 0.26,
      "openness": 0.18
    },
    "cue_spans": [
      {"text": "不一定", "signal": "skepticism", "kind": "hedge", "strength": 0.4}
    ]
  }
}
```

## Workflow

### 1. Screen

Run `screen` when you need a fast deterministic first pass from text, history, and runtime hints.

```bash
python scripts/emotion_engine.py screen --input turn.json --pretty
```

Use this stage to get:

- `features`
- `initial_vector`
- `emotion_vector`
- `evidence`
- `labels`

### 2. Confirm

Run `confirm` after you have either:

- the `screen` result only
- the `screen` result plus an LLM semantic judgment

```bash
python scripts/emotion_engine.py confirm --input turn.json --pretty
```

Use this stage to produce the final state that should drive behavior:

- `confirmed_state`
- `dominant_mode`
- `emotion_vector`
- `mode_scores`
- `confidence`
- `ttl_seconds`
- `weight_schedule`
- `consistency_snapshot`

### 3. Predict

Run `predict` or `run` to estimate where the conversation is heading.

Prediction covers:

- task complexity
- frustration risk
- stall risk
- patience window
- next update deadline
- semantic pass budget
- baseline-aware delay budget
- hidden hook mode

### 4. Guide

Use `guidance.question` only when the user state is unclear or tension is rising and a short probe can improve alignment.

Keep the question short. Ask for one dimension at a time:

- result first vs explanation first
- speed vs certainty
- where the user is stuck

### 5. Route

Use `routing.thread_interface` to drive orchestration.

Key fields:

- `queue_mode`
- `prefer_main_thread`
- `defer_heartbeat`
- `allow_parallel_subagents`
- `progress_update_interval_sec`
- `openclaw`
- `hermes`

## Emotion Model

The engine keeps three layers:

- `emotion_vector`: concurrent affect axes. Current axes are `urgency`, `frustration`, `confusion`, `skepticism`, `satisfaction`, `cautiousness`, `openness`.
- `interaction_state`: task-reading axes. Current axes are `clarity`, `trust`, `engagement`.
- `constraint_signals`: execution constraints. Current axes are `boundary_strength`, `verification_preference`, `scope_tightness`, `evidence_requirement`.

Each axis is continuous and concurrent.
`0.8` means the axis is currently dominant enough to steer runtime behavior.

Intensity bands:

- `0.00-0.29`: background
- `0.30-0.54`: present
- `0.55-0.74`: strong
- `0.75-1.00`: dominant

Use `mode_scores` to decide which mode should win orchestration when several emotions are present at once.

## Dynamic Pre-Prompt

Insert `overlay_prompt` as a compact dynamic system or developer overlay for the next turn.

Use it for:

- reply style changes
- verification intensity
- update cadence
- background work suppression
- guard mode after success

Use `debug_overlay_prompt` only for inspection or logging.

Use `profile_state` as the session-global baseline snapshot.
Use `constraint_signals` for boundary strength, verification preference, and scope tightness.
Use `memory_update` as an optional host-owned profile update payload.
Recommended storage is a bounded local JSON or sqlite profile owned by the host runtime.
It tracks:

- user timezone and local hour
- work-hours window
- effective delay budget
- current style shift versus baseline
- EMA-ready baseline update proposal
- EMA-ready `proposed_calibration_state`

`consistency_rate` is the long-run front versus posthoc吻合率。
系统会在冷启动阶段优先采信后置反问，当 `consistency_rate` 和 `consistency_samples` 升高后，自动抬升前置情绪标签的采信权重。

宿主侧的 profile store 可以通过 `user_profile.persona_traits`、`user_profile.big5`、`user_profile.affective_prior` 回填这些字段。
这些值只作为当前这一轮的低权重先验。

The host profile store can feed the engine through `user_profile.persona_traits`, `user_profile.big5`, and `user_profile.affective_prior`.
These values stay low-weight priors for the current turn.

Do not make it the permanent personality. Treat it as per-turn state.

## OpenClaw And Hermes

Read `references/integration-openclaw-hermes.md` when wiring the output into runtime hooks.

Use this mapping:

- OpenClaw: `message_received` or `before_agent_start` computes state, `agent:bootstrap` or `before_agent_start` injects the overlay, queue and subagent logic consume `thread_interface`.
- Hermes: keep the stable baseline in your runtime personality config, keep longer-lived user tendencies in a host profile store, and apply the per-turn state through `/personality`, local orchestration, or tool-driven overlays.

## Resources

- `scripts/emotion_engine.py`: screening, confirmation, prediction, guidance, overlay, and routing CLI.
- `scripts/minimal_host_adapter.py`: minimal host adapter with host-owned local profile reuse for `user_profile`, `last_state`, and `calibration_state`.
- `scripts/smoke_test.py`: scenario smoke tests with local history, host-adapter round-trip, and randomized community-style samples.
- `scripts/independent_audit.py`: independent audit checks for contracts, CLI ergonomics, host-profile boundaries, and false-positive guards.
- `scripts/marketplace_tag_audit.py`: marketplace-scope regression, evaluation, and smoke checks for listing metadata.
- `scripts/ablation_test.py`: real-world community-case ablation against a no-skill baseline.
- `scripts/posthoc_calibration_pack.py`: build the v2 cold-start posthoc calibration pack from community issue samples.
- `demo/local_history_event.json`: realistic local-history payload for demo, smoke, and adapter testing.
- `assets/community-posthoc-calibration-v2.jsonl`: expanded community-style calibration set with GitHub issues, discussions, and forum-style failure reports.
- `assets/community-posthoc-calibration-56.jsonl`: frozen first-pass snapshot for reproducibility.
- `references/examples.md`: side-by-side examples that show how the layer changes agent behavior.
- `references/model-prompts.md`: prompt blocks for initial screen, confirmation, and guidance.
- `references/prompt-chain-audit.md`: condensed design logic for external review and critique.
- `references/research-cues-v2.md`: source-backed notes for punctuation, textisms, pauses, misspellings, and confidence weighting.
- `references/emotion-value-model.md`: what this layer changes in routing, work quality, guard mode, and user alignment.
- `references/emotion-policy-matrix.md`: mapping from emotion state to behavior.
- `references/integration-openclaw-hermes.md`: runtime wiring notes and example flow.
