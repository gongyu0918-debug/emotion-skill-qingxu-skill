# Integration Notes For OpenClaw And Hermes

## OpenClaw

Recommended flow:

1. `message_received` or `before_agent_start` collects:
   - latest user message
   - recent visible history
   - runtime pressure data
2. Run:

```bash
python skills/emotion-orchestrator/scripts/emotion_engine.py run --input turn.json --output emotion.json
```

3. Use `overlay_prompt` in:
   - `before_agent_start`, or
   - `agent:bootstrap` if you want the overlay appended as a small extra context block
4. Apply `routing.thread_interface.openclaw` to:
   - queue mode
   - heartbeat suppression or deferral
   - `sessions_spawn` policy
   - progress update cadence
5. After posthoc reflection returns, merge `memory_update.proposed_calibration_state` into your durable calibration store.

Suggested mapping:

- `queue_mode=interrupt`: newest urgent human message should preempt slow background work
- `queue_mode=steer`: steer the current run at the next tool boundary
- `prefer_main_thread=true`: do not bury the user behind subagent chatter
- `allow_parallel_subagents=false`: collapse to the main thread unless exploration is explicitly useful
- `defer_heartbeat=true`: move heartbeat and low-priority scans behind the active user turn

## Hermes

Recommended flow:

1. Keep the long-lived voice in `SOUL.md`.
2. Keep durable user tendencies in `USER.md`.
3. Treat emotion output as a turn-local overlay.
4. Map `routing.thread_interface.hermes.personality` to a short-lived `/personality` or equivalent orchestration state.
5. Use `guidance.question` only when the state is unclear enough to justify one short probe.
6. Merge `memory_update.proposed_baseline` into `USER.md` or another durable store with EMA.
7. Feed `USER.md` back through `user_profile.persona_traits`, `user_profile.big5`, and `user_profile.affective_prior`.
8. Persist `memory_update.proposed_calibration_state` beside `USER.md` so front or posthoc trust can evolve per user.

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
  "confirmed_state": {},
  "prediction": {},
  "guidance": {},
  "routing": {
    "thread_interface": {
      "queue_mode": "steer",
      "prefer_main_thread": true,
      "defer_heartbeat": true,
      "allow_parallel_subagents": false,
      "progress_update_interval_sec": 15,
      "openclaw": {},
      "hermes": {}
    }
  },
  "overlay_prompt": "<emotion_context>...</emotion_context>"
}
```

Consume only what your runtime supports. Ignore the rest.
