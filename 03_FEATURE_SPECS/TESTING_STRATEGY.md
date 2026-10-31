# Testing Strategy

## Test layers

1. **Unit tests:** pure rules—duration, language, status transitions, routing policy, score calculations and invalidation.
2. **Integration tests:** database/repositories, file persistence, provider adapters (mocked and live smoke tests where credentials available), migrations, job lifecycle.
3. **Contract tests:** each original skill prompt's required input/output schema and prohibited behaviors; use original authoritative prompts and known test cases.
4. **UI tests:** create/edit project, source state, approval gating, destructive confirmations, errors and key masking.
5. **Security tests:** secrets absent from Git, logs, exports, UI and exception output; cross-project isolation.
6. **Acceptance tests:** complete user workflows from clean install through generation/export/deletion.
7. **Regression tests:** after each later phase, all previous phase tests continue passing.

## Required testing behavior

- Deterministic tests use fake providers and fixtures; do not incur real API cost.
- Live provider smoke tests are clearly separated and require valid credentials/user action.
- Test all boundary values (e.g. each exact approved vertical duration, 179/180 seconds landscape, part duration 0/8/>8).
- Test provider failure classes and ensure retry is bounded.
- Test old valid outputs stay intact when candidate output fails validation.
- Test source/script/setting changes invalidate the correct dependencies.
- Test concurrent project creation cannot exceed four active saved projects (DEC-019).
- Test execution history retention enforces strict 100-record cap per project with FIFO pruning upon 101st execution (DEC-018).
- Test execution history records store metadata only and strictly zero raw prompts, source text, or LLM request/response payloads (DEC-018).
- Test project deletion cascades to delete all linked execution history records while preserving shared `.env` file untouched (DEC-018).
- Test project A cannot read/write project B's data.
- Record command, environment, timestamp, result, relevant log excerpt and commit/PR for each acceptance run.
