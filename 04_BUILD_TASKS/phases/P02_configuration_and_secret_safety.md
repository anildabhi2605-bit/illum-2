# P02 — Configuration and secret safety

**Phase intent:** Implement local `.env` workflow requested by the user without exposing secrets or claiming encryption.

**Exit gate:** Configuration loads predictably, missing/invalid values fail safely, keys are masked/redacted, `.env` is ignored and tests detect secret leaks.

## Tasks (strict order)

### [P02-T01] Implement typed configuration loading
- **Goal:** Load `.env` and validated application settings safely at startup.
- **Prerequisites:** P01 complete; P00 decisions.
- **Deliverables:** Configuration module and startup validation.
- **Acceptance:** Missing optional key does not crash app; invalid required config gives sanitized actionable error; secret values are not serialized.

### [P02-T02] Harden repository ignore rules and example config
- **Goal:** Prevent accidental commits of local secrets/data.
- **Prerequisites:** P01-T01; P02-T01.
- **Deliverables:** `.env.example`, `.gitignore`, secret hygiene check.
- **Acceptance:** `.env` and local data do not appear in tracked files; example contains no real token.

### [P02-T03] Implement key add/remove and restart semantics
- **Goal:** Meet requested Notepad-based local configuration workflow.
- **Prerequisites:** P02-T01; P02-T02.
- **Deliverables:** Config reload-on-start behavior and UI/help text.
- **Acceptance:** Add/change/remove works after restart; provider becomes unavailable when config removed; app remains usable.

### [P02-T04] Implement provider connection test boundary
- **Goal:** Provide a safe connection-test interface without leaking keys.
- **Prerequisites:** P02-T01; provider interface may be stubbed until P05.
- **Deliverables:** Connection-test service contract and UI status model.
- **Acceptance:** No secret displayed; unknown states marked unknown; only actually executed tests shown as passed.

### [P02-T05] Run configuration security acceptance tests
- **Goal:** Verify secret lifecycle end to end.
- **Prerequisites:** P02-T01–T04.
- **Deliverables:** Security test report and status evidence.
- **Acceptance:** Sentinel absent from outputs/logs/exports/track; remove/restart works; local plaintext limitation documented.

## Phase rule
Complete tasks in listed order. If a prerequisite or source artifact is absent, mark the affected task BLOCKED and do not pretend its acceptance tests passed. The phase is done only when every required task is verified and the exit gate has evidence.
