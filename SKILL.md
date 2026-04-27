---
name: emotion-skill
description: Emotion-aware orchestration for coding agents. Use when a coding agent needs to adapt behavior during repo debugging, scoped implementation, repeated-failure recovery, evidence-demanding review, cautious changes, or post-success stabilization. Detect urgency, frustration, skepticism, confusion, caution, satisfaction, and openness from the latest turn, dialogue history, retries, and delay pressure, then return overlay_prompt, route reasons, response constraints, reply style, verification depth, queue mode, progress cadence, and guard behavior.
metadata:
  openclaw:
    emoji: "🎛️"
    os: ["darwin", "linux", "win32"]
---

# Emotion Skill

Emotion Skill gives coding agents a small read-the-room router.

It turns user-state signals into execution policy:

- urgency -> stay on the main thread, shorten updates, act first
- frustration -> repair first, raise verification, keep progress visible
- skepticism -> show basis, exact checks, and failure path before edits
- caution -> tighten scope, protect config, verify before changing files
- confusion -> explain one next step and ask at most one clarifier
- satisfaction -> switch to closeout, regression checks, and guard mode

The runtime output is JSON. Hosts can consume it for prompt overlays, queue routing, verification depth, heartbeat cadence, response constraints, and post-success behavior.

## Quick Start

Run the compact host contract:

```bash
python scripts/emotion_engine.py host --message "Show me the basis before changing more files." --pretty
```

Run the bundled local-history demo:

```bash
python scripts/emotion_engine.py host --input demo/local_history_event.json --pretty
```

Run the install and published-bundle smoke:

```bash
python scripts/download_smoke.py
```

Preview host-side persistence without writes:

```bash
python scripts/minimal_host_adapter.py --event demo/local_history_event.json --store-dir .demo-store --view host --no-persist --pretty
```

## Host Output

Use `host` for real runtime wiring. It returns:

- `mode`: the primary orchestration mode for this turn.
- `labels`: concurrent user states.
- `overlay_prompt`: compact per-turn state hint.
- `route_reasons`: compact log codes for why routing changed.
- `response_constraints`: direct guardrails for the next reply.
- `routing.reply_style`: response posture.
- `routing.verification_level`: checking depth.
- `routing.queue_mode`: collect, steer, or interrupt.
- `routing.prefer_main_thread`: whether to keep work on the main thread.
- `routing.progress_update_interval_sec`: progress cadence.
- `satisfaction_lock`: post-success closeout guard.
- `state.emotion_vector`: current affect axes.
- `state.interaction_state`: clarity, trust, and engagement axes.
- `state.state_delta`: cross-turn changes from `last_state`.
- `memory.should_persist`: host-side persistence recommendation.

Minimal host result shape:

```json
{
  "mode": "skeptical",
  "labels": ["frustrated", "skeptical"],
  "route_reasons": ["repeat_failure_pressure", "evidence_requested"],
  "response_constraints": ["show_basis_first", "name_verification_steps"],
  "overlay_prompt": "<state mode=skeptical ...>",
  "routing": {
    "reply_style": "evidence_then_act",
    "verification_level": "high",
    "queue_mode": "collect",
    "prefer_main_thread": true,
    "progress_update_interval_sec": 20
  }
}
```

## Input Contract

The top-level payload must be a JSON object. The smallest valid payload is:

```json
{
  "message": "latest user message"
}
```

Common production payload:

```json
{
  "message": "Only touch the parser file and show the failing path first.",
  "context": {
    "timezone": "Asia/Shanghai",
    "now_iso": "2026-04-27T10:00:00+08:00"
  },
  "history": [
    {"role": "user", "text": "earlier user turn"},
    {"role": "assistant", "text": "earlier assistant turn"}
  ],
  "runtime": {
    "response_delay_seconds": 20,
    "unresolved_turns": 3,
    "bug_retries": 2,
    "same_issue_mentions": 2,
    "queue_depth": 1,
    "background_tasks_running": 1
  },
  "last_state": {
    "vector": {},
    "emotion_vector": {},
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
  "user_profile": {
    "timezone": "Asia/Shanghai",
    "work_hours_local": [9, 22],
    "baseline": {
      "response_delay_seconds": 35,
      "politeness": 0.2,
      "terseness": 0.35,
      "punctuation": 0.15,
      "directness": 0.3
    },
    "persona_traits": {
      "patience": 0.55,
      "skepticism": 0.48,
      "caution": 0.52,
      "openness": 0.44,
      "assertiveness": 0.38
    }
  },
  "llm_semantic": {
    "labels": ["skeptical"],
    "confidence": 0.78,
    "emotion_vector": {
      "urgency": 0.18,
      "frustration": 0.12,
      "confusion": 0.08,
      "skepticism": 0.92,
      "satisfaction": 0.04,
      "cautiousness": 0.18,
      "openness": 0.12
    }
  }
}
```

Malformed JSON, missing files, and top-level arrays return exit code `2` with a single-line error.

## Output Modes

| Command | Purpose |
|---|---|
| `host` | compact runtime contract |
| `run` | full diagnostics |
| `screen` | deterministic first pass |
| `confirm` | final state and weight schedule |
| `predict` | risk, stall, patience, and semantic-pass budget |
| `route` | routing only |
| `guide` | short-probe guidance |
| `overlay` | overlay prompt inspection |
| `posthoc` | review-pass and calibration inspection |

## Emotion Model

The engine keeps three concurrent layers:

- `emotion_vector`: `urgency`, `frustration`, `confusion`, `skepticism`, `satisfaction`, `cautiousness`, `openness`
- `interaction_state`: `clarity`, `trust`, `engagement`
- `constraint_signals`: `boundary_strength`, `verification_preference`, `scope_tightness`, `evidence_requirement`

Intensity bands:

- `0.00-0.29`: background
- `0.30-0.54`: present
- `0.55-0.74`: strong
- `0.75-1.00`: dominant

Use `mode_scores` in the full `run` output when tuning arbitration between concurrent states.

## Integration Pattern

1. Run `host` when a user turn arrives.
2. Insert `overlay_prompt` into the current agent turn.
3. Feed `routing` into queue priority, thread choice, heartbeat deferral, progress cadence, and subtask policy.
4. Feed `response_constraints` into the next reply.
5. Apply `satisfaction_lock` after success to keep the agent in closeout and regression mode.
6. Persist `memory.proposed_calibration_state` only in a host-owned profile store.

Use [references/integration-openclaw-hermes.md](./references/integration-openclaw-hermes.md) for OpenClaw and Hermes wiring.

## Persistence Boundary

The core engine is stateless. It returns JSON, makes no network calls, and writes only when `--output` is provided.

The minimal host adapter writes these files under `--store-dir` when persistence is enabled:

- `user_profile.json`
- `last_state.json`
- `calibration_state.json`

Use `--no-persist` for read-only previews. Use `--ignore-bad-store` to skip corrupt store files and continue from empty store values.

## Language Coverage

Chinese and English have explicit calibration for:

- shared emotion cues
- community phrasing
- punctuation habits
- rhythmic pauses
- rushed typos
- coding-agent failure reports

Other languages use generic punctuation, repetition, delay, and structure signals.

## Scope

Use this skill for coding-agent orchestration during:

- repo debugging
- scoped implementation
- repeated-failure recovery
- evidence-demanding review
- cautious file or config changes
- post-success stabilization

The marketplace copy should stay anchored to developer workflows:

- repository debugging
- agent runtime routing
- verification depth control
- thread and heartbeat coordination
- stabilization after success

## Published Bundle

ClawHub publish now ships the runtime-facing subset only:

- `SKILL.md`
- `README.md`
- `README.zh-CN.md`
- `CHANGELOG.md`
- `LICENSE`
- `agents/openai.yaml`
- `scripts/emotion_engine.py`
- `scripts/minimal_host_adapter.py`
- `scripts/download_smoke.py`
- `demo/local_history_event.json`
- `references/examples.md`
- `references/model-prompts.md`
- `references/emotion-value-model.md`
- `references/emotion-policy-matrix.md`
- `references/integration-openclaw-hermes.md`

The full GitHub repo keeps the heavier regression, audit, and calibration assets.

## Validation

Published-bundle smoke:

```bash
python scripts/download_smoke.py
```

Full GitHub validation:

```bash
python scripts/alignment_test.py
python scripts/ablation_test.py
python scripts/smoke_test.py --seed 20260424 --strict
python scripts/independent_audit.py
python scripts/marketplace_tag_audit.py
python scripts/feature_gate_audit.py
python scripts/bundle_manifest_check.py
```

## Resources

Bundled with the published skill:

- `scripts/emotion_engine.py`: runtime engine and CLI.
- `scripts/minimal_host_adapter.py`: host-owned local profile adapter.
- `scripts/download_smoke.py`: install and published-bundle smoke check.
- `demo/local_history_event.json`: realistic local-history payload.
- `references/examples.md`: side-by-side examples.
- `references/model-prompts.md`: prompt blocks for semantic passes.
- `references/emotion-value-model.md`: routing and quality impact.
- `references/emotion-policy-matrix.md`: state-to-behavior mapping.
- `references/integration-openclaw-hermes.md`: runtime wiring notes.

Kept in the GitHub repo for deeper review and local validation:

- `scripts/smoke_test.py`: scenario and community smoke coverage.
- `scripts/independent_audit.py`: contract and host-boundary audit.
- `scripts/marketplace_tag_audit.py`: marketplace-scope regression.
- `scripts/bundle_manifest_check.py`: published-bundle manifest audit.
- `scripts/ablation_test.py`: skill-vs-baseline harness.
- `scripts/posthoc_calibration_pack.py`: calibration pack builder.
- `assets/community-posthoc-calibration-v2.jsonl`: expanded community calibration set.
- `assets/community-posthoc-calibration-56.jsonl`: frozen first-pass snapshot.
- `references/prompt-chain-audit.md`: design audit notes.
- `references/research-cues-v2.md`: source-backed cue notes.
