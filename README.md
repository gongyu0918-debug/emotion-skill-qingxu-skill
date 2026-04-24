# Emotion Skill

[简体中文 README](./README.zh-CN.md)

Emotion Skill is a small routing layer for coding agents. It reads the latest user turn, optional history, runtime pressure, and a local profile, then returns concrete instructions for how the agent should work this turn.

It helps an agent notice signals like "this is still broken", "show me the basis", "keep the scope tight", or "this works now, finish cleanly" and convert them into queue priority, verification depth, reply style, progress cadence, guard behavior, and compact route reasons.

## What Changes

| User state | Agent behavior |
|---|---|
| Urgent or blocked | stay on the main thread, shorten progress updates, act first |
| Frustrated after repeated failures | repair first, explain after, raise verification |
| Skeptical or asking for evidence | show basis, exact checks, and failure path before edits |
| Cautious about scope | verify first, keep changes narrow, protect files and config |
| Confused by the path | explain the next step, use one clarifier at most |
| Satisfied after success | switch into guard mode and prevent drift |

## 30-Second Demo

Run the compact host contract:

```bash
python scripts/emotion_engine.py host --message "This is still not fixed. Show me the basis before changing more files." --pretty
```

Example shape:

```json
{
  "mode": "skeptical",
  "labels": ["frustrated", "skeptical"],
  "route_reasons": ["runtime_priority", "repeat_failure_pressure", "evidence_requested"],
  "response_constraints": ["show_basis_first", "name_verification_steps", "avoid_guessing"],
  "overlay_prompt": "<state mode=skeptical ...>",
  "routing": {
    "reply_style": "evidence_then_act",
    "verification_level": "high",
    "queue_mode": "collect",
    "prefer_main_thread": true,
    "progress_update_interval_sec": 20
  },
  "memory": {
    "should_persist": false
  },
  "state": {
    "state_delta": {
      "available": false,
      "dominant_shift": "new_turn"
    }
  }
}
```

Use the bundled local-history event:

```bash
python scripts/emotion_engine.py host --input demo/local_history_event.json --pretty
```

Preview the host adapter without writing profile state:

```bash
python scripts/minimal_host_adapter.py --event demo/local_history_event.json --store-dir .demo-store --view host --no-persist --pretty
```

## Integration

Use these fields first:

- `overlay_prompt`: add this compact state hint to the current agent turn.
- `routing.reply_style`: choose the response posture, such as `repair_then_explain`, `evidence_then_act`, or `verify_then_act`.
- `routing.verification_level`: choose how much checking to do before acting.
- `routing.queue_mode`: choose whether to collect, steer, or interrupt work.
- `routing.progress_update_interval_sec`: set the progress update cadence.
- `route_reasons`: log why the route changed without exposing raw user text.
- `response_constraints`: feed direct guardrails into the next agent response.
- `satisfaction_lock`: keep successful work in closeout/regression mode.
- `state.state_delta`: compare this turn with the previous host-owned state.
- `memory.should_persist`: decide whether the host should merge the proposed profile update.

Minimal event:

```json
{
  "message": "This is still not fixed. Show me the basis before changing more files.",
  "history": [
    {"role": "assistant", "text": "I think I found the root cause."}
  ],
  "runtime": {
    "response_delay_seconds": 20,
    "unresolved_turns": 3,
    "bug_retries": 2,
    "same_issue_mentions": 2
  }
}
```

The full contract and advanced fields live in [SKILL.md](./SKILL.md).

## User Experience Boundary

The core engine is stateless. It returns JSON and writes nothing by itself.

The new host control fields are derived codes and small numeric deltas. They are safe to ignore in older hosts and useful for silent improvements in newer hosts:

- route logging: `route_reasons`
- reply shaping: `response_constraints`
- post-success drift control: `satisfaction_lock`
- cross-turn trend detection: `state.state_delta`

The minimal host adapter can persist three host-owned JSON files when you want cross-turn adaptation:

- `user_profile.json`
- `last_state.json`
- `calibration_state.json`

Use `--no-persist` for read-only previews. Use `--view host` for the compact output a real runtime usually needs.

## Install

Requirements:

- Python `3.9+`
- standard library only

Clone the repo:

```bash
git clone https://github.com/gongyu0918-debug/emotion-skill-qingxu-skill.git
cd emotion-skill-qingxu-skill
```

Optional local skill install for Codex-style skill loading.

macOS / Linux:

```bash
cp -r . ~/.codex/skills/emotion-skill
```

PowerShell:

```powershell
Copy-Item -LiteralPath . -Destination $HOME\.codex\skills\emotion-skill -Recurse -Force
```

## Output Model

The compact `host` output uses these fields:

- `state.emotion_vector.confusion`: user uncertainty or disorientation.
- `state.interaction_state.clarity`: task clarity inferred from wording and context.
- `state.state_delta`: significant cross-turn changes compared with `last_state`.
- `labels`: concurrent states that matter this turn.
- `mode`: the state that drives routing for this turn.

The full `run` output keeps the same values under `confirmed_state.*` and adds diagnostics, prompts, feature signals, and review plans.

## Current Checks

Current local run in this repo:

- alignment regression: `70/70`
- curated ablation harness: `333/333`
- static baseline in the same harness: `18/333`
- randomized community smoke: `24/24 strict` plus five `12/12 strict` seed runs
- independent audit: `ok`
- marketplace tag audit: `ok`
- feature gate audit: `ok`

These numbers are regression coverage from repository-owned cases. They are useful for catching behavior drift during development.

## Repo Layout

Runtime-facing files:

- [SKILL.md](./SKILL.md): skill definition and full contract
- [scripts/emotion_engine.py](./scripts/emotion_engine.py): runtime engine and CLI
- [scripts/minimal_host_adapter.py](./scripts/minimal_host_adapter.py): host adapter with optional local profile persistence
- [demo/local_history_event.json](./demo/local_history_event.json): realistic local-history demo event
- [references/examples.md](./references/examples.md): example turns and outcomes

Evaluation and audit files:

- [scripts/alignment_test.py](./scripts/alignment_test.py): curated regression suite
- [scripts/ablation_test.py](./scripts/ablation_test.py): skill-vs-baseline harness
- [scripts/smoke_test.py](./scripts/smoke_test.py): scenario and community smoke coverage
- [scripts/independent_audit.py](./scripts/independent_audit.py): contract and host-boundary audit
- [scripts/marketplace_tag_audit.py](./scripts/marketplace_tag_audit.py): marketplace-scope audit
- [scripts/posthoc_calibration_pack.py](./scripts/posthoc_calibration_pack.py): posthoc pack builder

ClawHub publishes the runtime-facing subset. GitHub keeps the full evaluation surface.

## License

Published bundles on ClawHub follow the platform-wide `MIT-0` terms.

The GitHub repository keeps its own [LICENSE](./LICENSE) file.
