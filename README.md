# 情绪.skill / Emotion Skill

[简体中文 README](./README.zh-CN.md)

> Teach your agent to read the room.

This is an orchestration layer for coding agents.

It turns urgency, frustration, skepticism, caution, satisfaction, and confusion into runtime behavior. The point is not nicer wording. The point is better execution.

[Install](#install) · [Invocation](#invocation) · [What it changes](#what-it-changes) · [Examples](#examples) · [Prompt chain review](#prompt-chain-review)

---

## What this is

This skill changes how an agent works:

- when to grab the main thread
- when to repair first and explain after
- when to show evidence before acting
- when to tighten scope
- when to stop pushing forward and switch into guard mode

The goal is simple: make an agent notice the human state behind the prompt.

---

## Install

### GitHub

```bash
git clone https://github.com/gongyu0918-debug/emotion-skill-qingxu-skill.git
cd emotion-skill-qingxu-skill
```

### Local skill install

macOS / Linux:

```bash
cp -r emotion-skill-qingxu-skill ~/.codex/skills/emotion-skill
```

PowerShell:

```powershell
Copy-Item -LiteralPath .\emotion-skill-qingxu-skill -Destination $HOME\.codex\skills\emotion-skill -Recurse -Force
```

### Run the engine directly

```bash
python scripts/emotion_engine.py run --input turn.json --pretty
```

### ClawHub

Once published:

```bash
clawhub install emotion-skill
```

---

## Invocation

### Invisible invocation

Wire it into `message_received` or `before_agent_start`.

The user says nothing special. The skill runs every turn.

### Out-of-box use

Feed one JSON payload into `emotion_engine.py`.

Use:

- `overlay_prompt`
- `routing.thread_interface`

That is enough to wire it into prompts, queueing, heartbeat, and subagent routing.

### Background analysis

Run the posthoc reflection behind the turn.

It quietly extracts emotional wording, stance shifts, and correction signals without interrupting the user.

---

## Language coverage

The current specialized calibration covers two languages:

- Chinese
- English

These two tracks already include shared emotion cues, community corpora, punctuation habits, pause rhythm, rushed typos, misspellings, and agent-user complaint patterns.

Other languages currently get light support through:

- generic punctuation intensity
- repetition and pause rhythm
- delay pressure
- repeated unresolved turns
- imperative structure

The repository and release notes should say this plainly: the current version does not include language-specific tuning for languages beyond Chinese and English.

---

## What it changes

| State | Agent behavior | Why it matters |
|---|---|---|
| `urgent` | prioritizes the main thread, shortens update interval, defers heartbeat | faster first useful action |
| `frustrated` | repairs first, explains after, raises verification | less drift, less wasted talk |
| `skeptical` | gives evidence and validation points first | fewer blind patches |
| `cautious` | tightens scope and prefers safer paths | fewer scope violations |
| `satisfied` | switches into guard mode | fewer regressions after success |

So the real value lands in four places:

1. priority
2. verification
3. explanation style
4. post-success stabilization

---

## How emotion is collected

Three layers.

### 1. Front screen

It reads:

- wording
- punctuation
- shortness
- typos and spelling errors
- repetition
- response delay
- repeated unresolved turns
- contradictions against recent context

### 2. Posthoc reflection

It asks one short hidden question:

What emotional wording, stance marker, correction cue, or tempo clue appeared in the latest message?

This is where weak shifts get caught:

- `not necessarily`
- `maybe`
- `are you sure`
- `show me the basis`
- `Fine.`

### 3. Persistent memory

It learns the user’s baseline:

- delay tolerance
- terseness
- skepticism
- caution
- openness

---

## Dynamic weighting

This skill does not keep a fixed trust ratio.

Cold start trusts posthoc more because the user profile is thin.

Over time it watches one core signal:

- `consistency_rate`

That is the long-run agreement between front and posthoc.

High agreement lifts front trust.
Low agreement keeps posthoc in charge.

That is what makes it user-specific.

---

## Examples

Full examples live in [references/examples.md](./references/examples.md).

### Example 1: Long delay, same issue again

User:

```text
Pick up where you left off. This is still not fixed. No response for several minutes.
```

Without the layer:

```text
I will continue investigating the issue.
```

With the layer:

```text
I am treating this as high priority. I will inspect the stuck step first and report one concrete failure point before changing anything else.
```

### Example 2: Mild skepticism

User:

```text
但是不一定，先给我依据。
```

Without the layer:

```text
The answer keeps flowing from the old assumption.
```

With the layer:

```text
I will give the basis and one validation point first, then the action path.
```

### Example 3: Success, then lock it down

User:

```text
主流程已经好了，继续收口，把配置守住。
```

Without the layer:

```text
The agent keeps generalizing changes.
```

With the layer:

```text
Switching into guard mode: smoke check, boundary lock, regression prevention, and drift prevention.
```

---

## Prompt chain review

This project started from a human prompt chain.

The architecture and implementation were completed with AI assistance, but the core design question came from a human observation:

- AI has no emotion
- users do
- users often reveal state without noticing it
- that state changes what a good answer should look like

The condensed review document is here:

- [references/prompt-chain-audit.md](./references/prompt-chain-audit.md)

It now explicitly contains the `VIBE CODING chain / prompt condensation` version of the design logic.

It is written so other people can challenge the chain directly.

---

## Current status

- alignment regression: `26/26`
- community ablation: `78.05%`
- no-skill baseline: `4.88%`
- community posthoc calibration cases: `56`

---

## Repo layout

- [SKILL.md](./SKILL.md): skill definition
- [scripts/emotion_engine.py](./scripts/emotion_engine.py): runtime engine
- [scripts/alignment_test.py](./scripts/alignment_test.py): alignment regression
- [scripts/ablation_test.py](./scripts/ablation_test.py): skill vs baseline comparison
- [scripts/posthoc_calibration_pack.py](./scripts/posthoc_calibration_pack.py): posthoc calibration pack builder
- [references/emotion-value-model.md](./references/emotion-value-model.md): why this layer matters

---

## License

MIT License.

Public, inspectable, and easy to reuse.
