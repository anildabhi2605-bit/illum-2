# P13 — Export, deletion, security and core integration acceptance

**Phase intent:** Harden core workflows before optional research features.

**Exit gate:** Core flow, project deletion, data-only export, secret scanning and regression suite pass.

## Tasks (strict order)

### [P13-T01] Implement data-only project ZIP export
- **Goal:** Package approved project artifacts without secrets or restore behavior.
- **Prerequisites:** P09–P12; data model stable.
- **Deliverables:** Export service and archive schema.
- **Acceptance:** Required content present; secrets absent; no restore endpoint/UI.

### [P13-T02] Implement safe project deletion and cleanup
- **Goal:** Delete linked data safely while protecting against partial loss.
- **Prerequisites:** P03/P04; cleanup service.
- **Deliverables:** Deletion orchestration and cleanup report.
- **Acceptance:** No accidental delete on cancel; successful deletion cleans linked data; failure does not leave unexplained partial loss.

### [P13-T03] Run security and project-isolation review
- **Goal:** Audit secret handling, storage scope, logs, routes and export.
- **Prerequisites:** P02–P13 artifacts.
- **Deliverables:** Security report with findings and fixes.
- **Acceptance:** No known critical secret exposure, cross-project access or unsafe local network exposure.

### [P13-T04] Run core full end-to-end acceptance
- **Goal:** Test the smallest full approved workflow on clean local data.
- **Prerequisites:** P09–P13 prior tasks.
- **Deliverables:** Core end-to-end acceptance report.
- **Acceptance:** All core critical tests pass; no unapproved feature gap silently waived.

### [P13-T05] Finalize retention, diagnostics and backup notes
- **Goal:** Make local operation failures supportable without leaking user data.
- **Prerequisites:** P06/P13-T01–T03.
- **Deliverables:** Operations/retention note and tests.
- **Acceptance:** Logs and temp files are bounded/redacted; user understands backup/export limits.

## Phase rule
Complete tasks in listed order. If a prerequisite or source artifact is absent, mark the affected task BLOCKED and do not pretend its acceptance tests passed. The phase is done only when every required task is verified and the exit gate has evidence.
