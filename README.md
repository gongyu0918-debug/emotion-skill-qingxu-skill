# Emotion Skill

[简体中文](./README.zh-CN.md) · [GitHub](https://github.com/gongyu0918-debug/emotion-skill-qingxu-skill) · `clawhub install emotion-skill`

Markdown-first guidance for coding agents under pressure.

Emotion Skill helps an agent choose better behavior when a coding task becomes
tense, blocked, ambiguous, or ready to close. The installed skill is an
agent-readable playbook: `SKILL.md` routes to focused files in `references/`.
Python scripts in this repository are maintainer validation tools, not the skill's
runtime control plane.

## Why People Install It

Coding agents often fail in the same human moments:

- The user says the same bug still happens, and the agent keeps explaining.
- The user asks for evidence, and the agent keeps guessing.
- The user protects scope, and the agent touches nearby files.
- The user gets no progress signal during a silent tool or queue delay.
- The user says it works, and the agent starts a new refactor.

This skill turns those moments into readable routing and response rules.

## Structure

Published ClawHub bundle:

- `SKILL.md`: trigger description, workflow, and reference index
- `agents/openai.yaml`: UI metadata and starter prompt
- `references/routing-playbook.md`: main state routing and tie breakers
- `references/response-constraints.md`: evidence, scope, progress, closeout guardrails
- `references/real-scenarios.md`: real scenario families for regression thinking
- `references/model-prompts.md`: optional compact overlays for host prompts
- `references/integration-openclaw-hermes.md`: host integration guidance
- `references/examples.md`: before/after behavior examples
- `references/emotion-value-model.md`: rationale and measurement ideas

GitHub-only maintenance files:

- `scripts/`: regression, audit, scenario, and historical runtime validation
- `assets/`: calibration and long-tail corpus material
- `demo/`: local examples for legacy runtime checks
- historical and research references excluded from the installed bundle

## Use

In a skills-aware agent:

```text
Use $emotion-skill when the user asks for evidence, repeats a failed bug,
protects scope, waits through a delay, is confused by a path, or asks to close
out after success.
```

The agent should read `SKILL.md`, then load only the matching reference. It should
not run a Python classifier before applying the playbook.

## Validation

Repository validation:

```bash
python scripts/markdown_skill_audit.py
python scripts/real_scenario_replay.py
python scripts/bundle_manifest_check.py
python scripts/marketplace_tag_audit.py
python scripts/alignment_test.py
python scripts/ablation_test.py
python scripts/smoke_test.py --seed 20260424 --strict
python -m compileall -q scripts
git diff --check
```

Validation intent:

- Markdown audit checks that routing, disclosure, and publish boundaries are
  Markdown-first.
- Real scenario replay checks representative scenario families against the
  references, not one exact phrase.
- Bundle manifest check confirms ClawHub publishes the lean Markdown bundle.
- Legacy runtime tests remain as regression evidence that the old Python tooling
  was not accidentally broken while being moved out of the installed skill path.

## Design Boundary

This is a skill, not a plugin. A plugin or host may implement automation around
the guidance, but the installed skill itself should remain useful as Markdown
that a person or agent can read directly.

## License

MIT. See the [GitHub repository license](https://github.com/gongyu0918-debug/emotion-skill-qingxu-skill/blob/main/LICENSE).
