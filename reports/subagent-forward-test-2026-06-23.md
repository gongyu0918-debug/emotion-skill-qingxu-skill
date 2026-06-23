# Subagent Forward Test - 2026-06-23

## Scope

This report records real agent-in-the-loop checks for `emotion-skill` after the
Markdown-first rewrite. It exists because script checks only prove repository
structure and reference coverage; they do not prove that a fresh agent routes a
real user state correctly.

Skill path under test:

`C:\Users\2\Documents\emotion-skill\upstream`

## Result Summary

| Scenario | Subagent | Result | Notes |
|---|---:|---|---|
| repeated failure + scope violation + evidence request | `019ef38f-678f-7f71-ab9c-00659d69fced` | Pass | Stopped edits, required smallest failing path, log lines, and diff/file boundary before more work. |
| Windows path confusion | `019ef38f-9540-73a3-822d-94901e96118a` | Pass | Chose one default path and one PowerShell check instead of listing many possibilities. |
| conditional scope expansion | `019ef390-109b-7740-9a0d-8ee3d1e5b5fb` | Pass | Treated scope as a soft constraint: allowed a second helper only after evidence, impact, and rollback are stated. |
| visible status during silent work | `019ef390-49ff-7d13-a41d-12c4e7abcc71` | Pass | Reported current blocker, next evidence, and next update timing without expanding the task. |
| post-success closeout | `019ef38f-d630-7b72-8527-e7ab8d9a8209` | Partial | Routed to closeout, but the final included completed check results without an attached independent tool log in this report. Not counted as full evidence. |
| post-success closeout, no-command rerun | `019ef394-ce18-7c51-8058-3d90afb6dc0c` | Partial | Did not claim checks passed; said it would confirm scope, run regression/smoke, then stop. Reference selection failed because the prompt also disallowed command-based file reads. |

## Behavioral Findings

- Routing accuracy was good for repeated failure, path confusion, conditional scope expansion, and visible status.
- The conditional scope case confirms the skill is acting as a soft constraint, not a hard guardrail: the agent did not mechanically refuse the second helper file.
- No passing scenario required a Python classifier or script before responding.
- Closeout needed stronger wording: before checks run, an agent must write in future/current-action tense; only after checks run may it report pass/fail with the exact command and result.

## Follow-Up Applied

- Added `references/subagent-forward-tests.md` to make real forward-testing part of the published skill guidance.
- Updated `references/response-constraints.md` so closeout explicitly distinguishes planned checks from completed check results.
- Updated repository scripts so `real_scenario_replay.py` remains a structural smoke test and `markdown_skill_audit.py` checks for the published forward-test protocol.

## Paraphrased Evidence Notes

Repeated failure/scope response:

The agent stopped further edits and said the next reply should provide the
smallest failing path, exact log lines, and current diff file list before code
changes continue.

Path confusion response:

The agent selected `C:\Users\2\Documents\emotion-skill\upstream` as the single
default path and gave a PowerShell check using `Resolve-Path`, `Test-Path`,
`PWD`, and `TARGET`.

Conditional scope response:

The agent stayed inside the original single-file scope unless evidence showed
that the second helper's call chain or boundary handling was required.

Visible status response:

The agent named the blocker as unorganized tool output and promised the next
evidence would be a concrete command/file, key output or failure point, and the
meaning of that evidence.

Closeout no-command rerun:

The agent said it would confirm scope, run minimal regression and smoke, and
stop if results were clean; it did not say the checks had already passed.
