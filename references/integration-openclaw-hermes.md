# Integration Notes For OpenClaw And Hermes

## OpenClaw

Recommended flow:

1. `message_received` or `before_agent_start` collects:
   - latest user message
   - recent visible history
   - runtime pressure data
2. Run:

```bash
python skills/emotion-skill/scripts/emotion_engine.py host --input turn.json --output emotion.json
```

Use full diagnostics while tuning:

```bash
python skills/emotion-skill/scripts/emotion_engine.py run --input turn.json --output emotion.full.json
```

3. Use `overlay_prompt` in:
   - `before_agent_start`, or
   - `agent:bootstrap` if you want the overlay appended as a small extra context block
4. Apply the compact `routing` fields to:
   - queue mode
   - heartbeat suppression or deferral
   - `sessions_spawn` policy
   - progress update cadence
5. Merge `memory.proposed_calibration_state` into a bounded host-owned calibration store.

Suggested mapping:

- `queue_mode=interrupt`: newest urgent human message should preempt slow background work
- `queue_mode=steer`: steer the current run at the next tool boundary
- `prefer_main_thread=true`: do not bury the user behind subagent chatter
- `allow_parallel_subagents=false`: collapse to the main thread unless exploration is explicitly useful
- `defer_heartbeat=true`: move heartbeat and low-priority scans behind the active user turn

## Hermes

Recommended flow:

1. Keep the long-lived voice in your runtime personality config.
2. Keep longer-lived user tendencies in a host-owned profile store.
3. Treat emotion output as a turn-local overlay.
4. Map `guidance.tone`, `routing.reply_style`, and `mode` to a short-lived `/personality` or equivalent orchestration state.
5. Use `guidance.question` only when the state is unclear enough to justify one short probe.
6. Use the full `run` output when you need `memory_update.proposed_baseline` for an EMA host profile store.
7. Feed the host profile store back through `user_profile.persona_traits`, `user_profile.big5`, and `user_profile.affective_prior`.
8. Store `memory_update.proposed_calibration_state` beside that profile so front-versus-review trust can evolve per user.

Suggested mapping:

- `concise`: urgent or frustrated
- `teacher`: confused
- `analytical`: skeptical
- `careful`: cautious
- `helpful`: neutral or satisfied

## Hook Contract

The emotion engine returns a stable structure:

```json
{
  "mode": "skeptical",
  "route_reasons": ["repeat_failure_pressure", "evidence_requested"],
  "response_constraints": ["show_basis_first", "name_verification_steps"],
  "guidance": {},
  "routing": {
    "reply_style": "evidence_then_act",
    "verification_level": "very_high",
    "queue_mode": "steer",
    "prefer_main_thread": true,
    "defer_heartbeat": true,
    "allow_parallel_subagents": false,
    "progress_update_interval_sec": 15
  },
  "overlay_prompt": "<state mode=skeptical ...>"
}
```

The compact `host` output is the recommended runtime contract. Raw labels stay out of that payload unless `host_capabilities.include_raw_emotion=true` is set for audit, in which case they appear under `diagnostics.internal.labels`. The full `run` output keeps deeper fields such as `confirmed_state`, `prediction`, `routing.thread_interface`, `memory_update`, and `debug_overlay_prompt`. Use `debug_overlay_prompt` for inspection logs.
