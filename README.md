# Emotion Skill

[简体中文 README](./README.zh-CN.md)

Emotion-aware routing for coding agents.

This repo reads the latest user turn plus optional history, runtime signals, and user profile, then returns work-mode signals such as priority, verification depth, reply style, guard mode, and review-pass hints.

## Included In This Repo

- `SKILL.md`: skill definition and full input contract
- `scripts/emotion_engine.py`: rule engine and CLI
- `scripts/alignment_test.py`: curated regression cases
- `scripts/ablation_test.py`: curated skill-vs-baseline harness
- `scripts/smoke_test.py`: scenario smoke tests with local history and randomized community workflows
- `scripts/independent_audit.py`: independent contract and host-profile checks
- `scripts/marketplace_tag_audit.py`: marketplace-tag regression, evaluation, and smoke checks
- `scripts/minimal_host_adapter.py`: minimal host adapter with a host-owned local profile
- `demo/local_history_event.json`: realistic demo payload
- `references/`: design notes, examples, prompt references

## Best Fit

- coding-agent turns with delivery pressure, repeated failures, skepticism, boundary protection, or post-success stabilization
- hosts that can call a local Python script and consume JSON

## Marketplace Scope

- repository debugging
- coding-agent orchestration
- verification depth control
- queue, thread, and heartbeat coordination
- stabilization after success

## Core Inputs

The engine accepts a JSON payload. The fields you will use most often are:

- `message`
- `history`
- `runtime`
- `user_profile`
- `last_state`
- `llm_semantic`
- `posthoc_semantic`
- `calibration_state`

Full contract and field examples live in [SKILL.md](./SKILL.md).

## Core Outputs

Start with these:

- `overlay_prompt`: compact runtime hint for the current turn
- `routing.thread_interface`: queue mode, main-thread preference, heartbeat behavior, parallelism, progress interval

Useful secondary outputs:

- `guidance`
- `memory_update`
- `posthoc_plan`
- `prompts`

## Install

Requirements:

- Python `3.9+`
- no external dependencies

Clone the repo:

```bash
git clone https://github.com/gongyu0918-debug/emotion-skill-qingxu-skill.git
cd emotion-skill-qingxu-skill
```

Optional local skill install for Codex-style skill loading.

macOS / Linux:

```bash
cp -r emotion-skill-qingxu-skill ~/.codex/skills/emotion-skill
```

PowerShell:

```powershell
Copy-Item -LiteralPath .\emotion-skill-qingxu-skill -Destination $HOME\.codex\skills\emotion-skill -Recurse -Force
```

## Quick Start

Smoke test with a single message:

```bash
python scripts/emotion_engine.py run --message "先给我依据，别瞎猜" --pretty
```

Run the bundled local-history demo:

```bash
python scripts/emotion_engine.py run --input demo/local_history_event.json --pretty
```

Run with a full payload:

```bash
python scripts/emotion_engine.py run --input path/to/turn.json --pretty
```

Minimal host adapter with a host-owned local profile:

```bash
python scripts/minimal_host_adapter.py --event demo/local_history_event.json --store-dir .demo-store --pretty
```

Minimal payload example:

```json
{
  "message": "This is still not fixed. Show me the basis before changing more files.",
  "history": [
    {"role": "assistant", "text": "I think I found the root cause"}
  ],
  "runtime": {
    "response_delay_seconds": 20,
    "unresolved_turns": 3,
    "bug_retries": 2,
    "same_issue_mentions": 2
  }
}
```

## Integration Path

1. Call `emotion_engine.py` on every user turn.
2. Insert `overlay_prompt` into the current turn as a compact runtime pre-prompt.
3. Apply `routing.thread_interface` to queueing, main-thread choice, heartbeat behavior, and progress cadence.
4. When `analysis.semantic_pass` is `fast`, run the model-side semantic pass and feed the result back as `llm_semantic`.
5. Reuse the bounded fields from `memory_update` inside a host-owned local profile if you want cross-turn adaptation.

## States It Optimizes For

| State | Main behavior change | Expected value |
|---|---|---|
| `urgent` | prioritize the main thread, shorten progress interval | faster first useful action |
| `frustrated` | repair first, explain after | lower drift and less wasted dialogue |
| `skeptical` | show basis and verification points first | fewer blind patches |
| `cautious` | tighten scope and prefer safer paths | fewer scope violations |
| `satisfied` | switch into guard mode | fewer regressions after success |

## Language Coverage

Specialized calibration currently focuses on:

- Chinese
- English

The generic path still uses punctuation intensity, repetition, delay pressure, unresolved-turn pressure, and imperative structure for other languages.

## Product Boundaries

- runtime adapters stay in the host layer
- cross-turn adaptation reuses bounded fields from `memory_update` inside a host-owned local profile
- benchmark numbers below come from curated internal cases
- first-turn judgments are strongest when `runtime` and `history` are present
- marketplace scope is coding-agent orchestration only

## Current Status

Current local run in this repo:

- alignment regression: `50/50`
- curated ablation harness: `201/201`
- static baseline in the same harness: `6/201`
- scenario smoke test: `ok`
- independent audit: `ok`
- marketplace tag audit: `ok`
- feature gate audit: `ok`

These numbers come from repository-owned curated cases and are best read as regression coverage, not production A/B evidence.

ClawHub publishes the runtime-facing subset only. The heavier regression, audit, and calibration assets stay in the GitHub repository.

## Repo Layout

Published on ClawHub:

- [SKILL.md](./SKILL.md): skill definition and full contract
- [scripts/emotion_engine.py](./scripts/emotion_engine.py): runtime engine
- [scripts/minimal_host_adapter.py](./scripts/minimal_host_adapter.py): minimal host adapter with a host-owned local profile
- [demo/local_history_event.json](./demo/local_history_event.json): realistic local-history demo payload
- [references/examples.md](./references/examples.md): example turns and outcomes

Kept in the GitHub repository:

- [scripts/alignment_test.py](./scripts/alignment_test.py): curated regression suite
- [scripts/ablation_test.py](./scripts/ablation_test.py): curated evaluation harness
- [scripts/smoke_test.py](./scripts/smoke_test.py): scenario smoke coverage
- [scripts/independent_audit.py](./scripts/independent_audit.py): independent verification
- [scripts/marketplace_tag_audit.py](./scripts/marketplace_tag_audit.py): marketplace-scope audit
- [scripts/posthoc_calibration_pack.py](./scripts/posthoc_calibration_pack.py): pack builder for cold-start posthoc cases

## Next

- stricter false-positive tests for short imperative turns
- host adapters for common agent runtimes
- richer demo payloads and installation walkthroughs
- broader calibration beyond Chinese and English

## License

Published bundles on ClawHub follow the platform-wide `MIT-0` terms.

The GitHub repository keeps its own [LICENSE](./LICENSE) file.
