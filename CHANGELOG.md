# Changelog

## 1.3.1 - 2026-06-23

- hardened host payload numeric parsing so malformed runtime, profile, calibration, and vector values degrade instead of crashing the engine
- fixed Windows local-hour handling when IANA timezone data is unavailable by using explicit `local_hour` or offset-bearing `now_iso`
- made the minimal host adapter reject events without a latest `message` before persistence
- aligned README, README.zh-CN, SKILL.md, and OpenClaw/Hermes integration notes with the current compact `host` contract
- turned alignment and ablation scripts into real failure gates and expanded independent audit coverage for bad numeric payloads and missing-message adapter events
- aligned runtime schema and upcoming GitHub/ClawHub release version to `1.3.1`

## 1.3.0 - 2026-05-02

- split the former monolithic runtime into focused modules for types, terms, features, scoring, routing, output, and shared helpers
- kept `scripts/emotion_engine.py` as the CLI and pipeline facade with the existing `host` / `run` behavior
- kept the 1.2 host contract shape, raw affect isolation, positive prompt addenda, profiling, logging, and route-reason truncation behavior
- reorganized `infer_labels` into named signal predicates and `dominant_mode` into an ordered rule table with stable rule ids
- updated README, README.zh-CN, SKILL.md, and the ClawHub runtime bundle manifest for the new module files
- this entry covers the local mainline refactor; GitHub Release and ClawHub publish are intentionally paused

## 1.2.4 - 2026-05-01

- reused the already computed profile state in `build_model_prompts` and passed real `features` into overlay rendering
- added visible degradation marking for truncated `route_reasons`
- added optional CLI profiling through `--profile` with pipeline stage timings in full `run` output
- added `--log-level` for stderr-only runtime logs while preserving JSON stdout
- added lightweight `TypedDict` boundaries for core pipeline maps and a dev-only `mypy.ini`
- added audit coverage for repeated-token regex, profile/log output, prompt overlay features, and route-reason truncation

## 1.2.3 - 2026-04-30

- marked `state.interaction_state` as a deprecated compatibility alias for top-level `interaction_state`
- changed raw diagnostics safety precedence so explicit payload `false` values override `--include-raw-emotion`
- added `INTERACTION_NEED_ENUM` validation for `state.state_delta.interaction.needs`
- added unsupported `context.language` / `runtime.language` degradation markers with English fallback
- expanded positive prompt leakage audit with English and Chinese negative-valence term files across all prompt-addendum modes
- removed negative-valence wording from the frustrated/urgent positive prompt templates

## 1.2.2 - 2026-04-27

- aligned the ClawHub published-bundle manifest with the real install surface by excluding the repository license file from the runtime package
- updated README and README.zh-CN license links to point at the GitHub repository license
- kept the ClawHub package focused on the 14 runtime-facing files plus ClawHub-generated install metadata

## 1.2.1 - 2026-04-27

- rewrote README and README.zh-CN as GitHub-facing landing pages with install, 30-second demo, host contract, raw affect opt-in, feedback loop, validation, and fit guidance
- rewrote SKILL.md as a ClawHub-facing runtime card with trigger scenarios, production host fields, input contract, audit mode, persistence boundary, integration pattern, and published-bundle manifest
- refreshed `agents/openai.yaml` listing copy to emphasize positive routing, evidence-first behavior, scope protection, progress visibility, and guarded closeout

## 1.2.0 - 2026-04-27

- changed default `host` output to keep raw `labels` and `state.emotion_vector` out of the production payload
- added `guidance.system_prompt_addendum` and `guidance.tone` so internal user-state signals route into positive action prompts
- added `host_capabilities.include_raw_emotion=true` / `--include-raw-emotion` for audit-only `diagnostics.internal.labels`, `diagnostics.internal.emotion_vector`, raw `state_delta`, and `mode_scores`
- changed host-facing `state.state_delta.dominant_shift` from affect wording such as `rising_frustration` / `falling_trust` to action wording such as `needs_concrete_unblock` / `needs_evidence_first`
- changed default host `state.state_delta.interaction` to expose action needs instead of raw signed interaction deltas
- added `runtime.last_routing_outcome` as a lightweight feedback channel for the next turn
- added `ROUTE_REASON_ENUM` validation at the route-reason exit
- hardened numeric clamping against non-finite values before host-facing output
- changed degradation reason finalization to dedupe and emit `degradation_reasons_truncated` when capped
- clarified `weight_schedule.weight_model=independent_signal_weights`
- fixed bundle manifest parsing to read only exact bullet items in the published-bundle section
- adapter now reports ignored corrupt store files through `adapter_warnings`

### Field-Level Diff

- `host.labels`: removed by default; available at `diagnostics.internal.labels` with raw opt-in
- `host.state.emotion_vector`: removed by default; available at `diagnostics.internal.emotion_vector` with raw opt-in
- `host.guidance.system_prompt_addendum`: added
- `host.guidance.tone`: added
- `host.interaction_state`: added as a top-level positive host-facing state
- `host.state.state_delta.dominant_shift`: renamed values to action names
- `host.state.state_delta.interaction`: changed from raw numeric deltas to `{changed, needs}`
- `run.host_capabilities`: added
- `runtime.last_routing_outcome`: added optional input

## 1.1.4 - 2026-04-27

- added friendly top-level JSON object errors for CLI and host adapter inputs
- added nested-directory atomic output writes for `emotion_engine.py` and `minimal_host_adapter.py`
- added `--ignore-bad-store` and path-specific corrupt store diagnostics to the minimal host adapter
- added `scripts/download_smoke.py` for install and published-bundle verification
- added `--strict` to `scripts/smoke_test.py`
- added published-bundle manifest auditing and refreshed integration paths for `emotion-skill`
- rewrote README and SKILL documentation around install speed, host contracts, trust recovery, and published-bundle validation
- clarified language coverage, persistence reset, validation commands, and MIT licensing

## 1.1.3 - 2026-04-24

- added compact `route_reasons` and `response_constraints` for host-side orchestration
- added `state.state_delta` to expose significant cross-turn shifts from `last_state`
- added `satisfaction_lock` for post-success closeout and regression-guard behavior
- expanded smoke and independent audits for the new host control fields

## 1.1.2 - 2026-04-24

- added a compact `host` CLI output for integration previews and runtime adapters
- added `--view host` and `--no-persist` to the minimal host adapter
- added audits for compact host output and read-only adapter preview mode

## 1.1.1 - 2026-04-23

- tightened payload normalization for mapping, label-list, and history fields
- capped `degradation_reasons` output to keep host-facing diagnostics bounded
- gated soft urgency phrases like `for several minutes` behind runtime or stall context
- added weight-schedule boundary audits and documented versioned runtime changes

## 1.1.0 - 2026-04-21

- added stable top-level contract fields such as `schema_version`, `degraded`, and `degradation_reasons`
- exposed `persona_source` and host-facing degradation signals for safer adapter integration
- removed wall-clock fallback from local-hour inference for deterministic replays
