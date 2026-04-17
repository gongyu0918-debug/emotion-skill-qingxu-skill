# Emotion Policy Matrix

## Emotion Axes

- `urgency`: how strongly the user wants immediate progress
- `frustration`: dissatisfaction with the current task state
- `confusion`: how much information gap or path uncertainty is present
- `skepticism`: how strongly the user is questioning the current claim, diagnosis, or proposed action
- `satisfaction`: whether the user feels the task is going well
- `cautiousness`: how strongly the user is signaling care, scope protection, or verification-first behavior
- `openness`: how much the user is inviting divergence, options, or exploration

## Interaction State

- `clarity`: how well the request specifies the goal and path
- `trust`: how much procedural tolerance the user is showing
- `engagement`: how invested the user is in the current topic

All emotion axes can coexist.
`dominant_mode` is the routing winner for the current turn.

## Modes

### urgent

Signals:

- short commands
- repeated催促 or repeated emphasis
- time pressure words
- rising delay pressure

Behavior:

- answer with action first
- keep the first response short
- prefer current thread over background work
- defer heartbeat and low-priority checks
- tighten progress update interval

### frustrated

Signals:

- anger terms
- harsh corrections
- repeated mention of the same unresolved issue
- long unresolved runtime

Behavior:

- raise verification depth
- stop speculative explanation
- acknowledge the problem state through action
- avoid parallel exploration unless it clearly shortens resolution time

### confused

Signals:

- high confusion
- vague goal words
- question-heavy messages
- contradictory constraints

Behavior:

- explain in steps
- surface assumptions explicitly
- ask one short disambiguation question when needed
- prefer teacher-style guidance

### satisfied

Signals:

- praise
- confirmation words
- "continue" after a successful milestone

Behavior:

- switch to guard mode
- stabilize outputs
- run a small drift-prevention or smoke-check pass
- avoid reopening solved branches

### skeptical

Signals:

- evidence-seeking wording
- direct challenge to a diagnosis or claim
- contradiction against the assistant's previous conclusion
- proof or source requests

Behavior:

- lead with basis before action
- avoid overclaiming
- surface one concrete verification point
- tighten claims to what is currently supported

### cautious

Signals:

- care language
- keep-scope-tight wording
- verify-first wording
- repeated safety or boundary emphasis

Behavior:

- prefer dry-run or verification-first flow
- ask for the missing boundary if needed
- lower parallelism

### exploratory

Signals:

- brainstorming
- open-ended comparison
- multi-option requests without time pressure

Behavior:

- allow wider search
- parallelize when it shortens synthesis time
- keep final recommendation decisive

## Routing Defaults

| Condition | Queue | Thread | Heartbeat | Parallelism | Reply style |
|---|---|---|---|---|---|
| urgent high | `steer` or `interrupt` | main | defer | low | `ack_then_act` |
| frustrated high | `steer` | main | defer | low | `repair_then_explain` |
| confused high | `collect` | main | normal | low | `explain_then_act` |
| skeptical high | `collect` | main | normal | low | `evidence_then_act` |
| satisfied high | `collect` | main | normal | low | `guard_then_close` |
| exploratory high | `collect` | current | normal | medium | `synthesize_then_recommend` |
| cautious high | `collect` | main | normal | low | `verify_then_act` |
