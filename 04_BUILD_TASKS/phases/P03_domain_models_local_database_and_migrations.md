# P03 — Domain models, local database and migrations

**Phase intent:** Create the database/domain baseline before workflow code depends on it.

**Exit gate:** Migrations work from empty DB and current DB; repositories scope by project; key invariants are unit/integration tested.

## Tasks (strict order)

### [P03-T01] Define domain entities and state enums
- **Goal:** Create typed project/source/script/job/output/approval domain contracts independent of UI.
- **Prerequisites:** P01 complete; P00 baseline.
- **Deliverables:** Domain types and validation functions.
- **Acceptance:** Illegal state/ratio/duration transitions are rejected centrally; IDs are unique; types map to requirements.

### [P03-T02] Implement database schema and migrations
- **Goal:** Persist project-isolated records with safe migration behavior.
- **Prerequisites:** P03-T01; stack decision.
- **Deliverables:** Initial schema and migration set.
- **Acceptance:** Empty database creates cleanly; constraints are enforced; no script-history table added; migration failure does not corrupt DB.

### [P03-T03] Implement project-scoped repositories
- **Goal:** Centralize access checks by `project_id`.
- **Prerequisites:** P03-T02.
- **Deliverables:** Repository layer with project scoping.
- **Acceptance:** Every project-owned read/write scoped; cross-project IDs cannot leak or mutate data.

### [P03-T04] Implement local files and temporary-data service
- **Goal:** Create safe paths for DB attachments, exports, logs and temp data.
- **Prerequisites:** P03-T02; P02 secret rules.
- **Deliverables:** Local file service and path rules.
- **Acceptance:** Files stay inside intended app directories; local data dirs excluded from Git; cleanup is testable.

### [P03-T05] Verify migrations, persistence and isolation
- **Goal:** Prove core persistence invariants before UI workflows.
- **Prerequisites:** P03-T01–T04.
- **Deliverables:** P03 test report.
- **Acceptance:** All schema/integrity tests pass; failures are reproducible; no later phase used to mask basic DB failures.

## Phase rule
Complete tasks in listed order. If a prerequisite or source artifact is absent, mark the affected task BLOCKED and do not pretend its acceptance tests passed. The phase is done only when every required task is verified and the exit gate has evidence.
