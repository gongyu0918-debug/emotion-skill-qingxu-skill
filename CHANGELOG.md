# Changelog

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
