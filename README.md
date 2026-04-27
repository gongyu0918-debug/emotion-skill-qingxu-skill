# Emotion Skill

[简体中文 README](./README.zh-CN.md)

Emotion Skill is a small orchestration layer for coding agents. It reads the latest user turn, recent history, runtime pressure, and optional local profile state, then returns a compact JSON contract that tells the agent how to work this turn.

It is built for the moments where a coding agent usually loses trust: repeated failures, vague stuck states, evidence requests, scope anxiety, and the handoff after success.

![Python](https://img.shields.io/badge/python-3.9%2B-3776AB)
![Dependencies](https://img.shields.io/badge/dependencies-standard%20library-2E7D32)
![License](https://img.shields.io/badge/license-MIT-blue)

## Why It Exists

The same coding request should route differently when the user state changes.

| User signal | Runtime behavior |
|---|---|
| "This is still broken" | keep the main thread focused, raise verification, shorten updates |
| "Show me the basis" | show evidence, exact checks, and failure path before edits |
| "Only touch this file" | tighten scope, avoid config drift, verify first |
| "I am confused" | explain the next step, ask at most one clarifier |
| "Works now, wrap it up" | enter guard mode, run regression checks, stop scope drift |

The output is intentionally boring: JSON fields your host can consume without exposing raw user text.

## Install

```bash
git clone https://github.com/gongyu0918-debug/emotion-skill-qingxu-skill.git
cd emotion-skill-qingxu-skill
python scripts/download_smoke.py
```

Requirements:

- Python `3.9+`
- standard library only

Optional local Codex-style skill install:

```bash
cp -r . ~/.codex/skills/emotion-skill
```

PowerShell:

```powershell
Copy-Item -LiteralPath . -Destination $HOME\.codex\skills\emotion-skill -Recurse -Force
```

## 30-Second Demo

```bash
python scripts/emotion_engine.py host --message "This is still not fixed. Show me the basis before changing more files." --pretty
```

Expected shape:

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
    "prefer_main_thread": true
  },
  "satisfaction_lock": {
    "active": false
  }
}
```

Run the bundled local-history event:

```bash
python scripts/emotion_engine.py host --input demo/local_history_event.json --pretty
```

Preview host-side persistence without writing state:

```bash
python scripts/minimal_host_adapter.py --event demo/local_history_event.json --store-dir .demo-store --view host --no-persist --pretty
```

## Host Contract

Use `host` for runtime integration. It returns the compact fields most hosts need:

- `overlay_prompt`: small per-turn state hint for the agent.
- `mode`: primary orchestration mode for this turn.
- `labels`: concurrent user states that matter this turn.
- `route_reasons`: compact route log safe for telemetry.
- `response_constraints`: direct guardrails for the next response.
- `routing.reply_style`: response posture such as `repair_then_explain`, `evidence_then_act`, or `verify_then_act`.
- `routing.verification_level`: checking depth before edits.
- `routing.queue_mode`: collect, steer, or interrupt work.
- `routing.progress_update_interval_sec`: progress cadence.
- `satisfaction_lock`: post-success guard and closeout behavior.
- `state.state_delta`: significant cross-turn shifts from host-owned state.
- `memory.should_persist`: recommendation for merging profile updates.

Minimal input:

```json
{
  "message": "This is still not fixed. Show me the basis before changing more files."
}
```

Useful optional fields:

```json
{
  "message": "Only touch the parser file and show the failing path first.",
  "history": [
    {"role": "assistant", "text": "I think the last patch fixed it."}
  ],
  "runtime": {
    "response_delay_seconds": 20,
    "unresolved_turns": 3,
    "bug_retries": 2,
    "same_issue_mentions": 2
  },
  "last_state": {},
  "calibration_state": {},
  "user_profile": {}
}
```

Top-level payloads must be JSON objects. Malformed JSON, missing files, and top-level arrays return exit code `2` with a single-line error.

## Output Modes

| Command | Use it for |
|---|---|
| `host` | runtime integration and compact host output |
| `run` | full diagnostics, prompts, features, prediction, and review plans |
| `screen` | deterministic first pass over text, history, and runtime hints |
| `confirm` | final state after rule screen and optional semantic input |
| `route` | routing-only inspection |
| `guide` | short-probe guidance |
| `overlay` | prompt overlay inspection |
| `posthoc` | review-pass and calibration debugging |

## Persistence Boundary

The engine itself is stateless. It returns JSON, makes no network calls, and writes only when `--output` is provided.

The minimal host adapter can persist three host-owned files under `--store-dir`:

- `user_profile.json`
- `last_state.json`
- `calibration_state.json`

Use `--no-persist` for read-only previews. Reset local adaptation by deleting those three files. Corrupt store files report the exact path; `--ignore-bad-store` skips corrupt store values and continues from empty state.

## Language Coverage

Chinese and English have explicit calibration for shared emotion cues, community phrasing, punctuation habits, pauses, rushed typos, and coding-agent failure reports.

Other languages use generic punctuation, repetition, delay, and structure signals. Treat those outputs as weaker routing hints.

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

Verified locally on 2026-04-27 with Python 3.11.9:

- alignment regression: `70/70`
- curated ablation harness: `333/333`
- static baseline in the same harness: `18/333`
- smoke strict: `ok`
- independent audit: `ok`
- marketplace tag audit: `ok`
- feature gate audit: `ok`
- download smoke: `ok`
- bundle manifest check: `ok`

## Published Bundle

ClawHub ships the runtime-facing subset:

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

The GitHub repository keeps the regression, audit, and calibration surface.

## Integration Notes

- OpenClaw and Hermes wiring: [references/integration-openclaw-hermes.md](./references/integration-openclaw-hermes.md)
- Behavior examples: [references/examples.md](./references/examples.md)
- Policy matrix: [references/emotion-policy-matrix.md](./references/emotion-policy-matrix.md)
- Value model: [references/emotion-value-model.md](./references/emotion-value-model.md)
- Model prompts: [references/model-prompts.md](./references/model-prompts.md)

## License

MIT. See [LICENSE](./LICENSE).
