# P15 — Regression, installation, packaging and release

**Phase intent:** Make the application releasable and repeatable.

**Exit gate:** Clean install, upgrade, migration, regression and optional package tests pass with published evidence.

## Tasks (strict order)

### [P15-T01] Run full regression and clean-install validation
- **Goal:** Prove the exact release commit works from a clean environment.
- **Prerequisites:** P13 accepted; P14 accepted if included.
- **Deliverables:** Release candidate test report.
- **Acceptance:** All mandatory tests pass on declared supported platform; unsupported platforms explicitly excluded.

### [P15-T02] Verify update and migration procedure
- **Goal:** Ensure existing local data survives supported application updates.
- **Prerequisites:** P15-T01; migration plan.
- **Deliverables:** Upgrade test and migration notes.
- **Acceptance:** Supported upgrade succeeds; failure is safe and actionable; `.env` remains untouched.

### [P15-T03] Build optional Windows executable
- **Goal:** Package Python runtime only after source-based install is stable.
- **Prerequisites:** P15-T01; packaging decision approved.
- **Deliverables:** Signed/versioned executable artifact or documented decision to defer.
- **Acceptance:** Clean target environment runs it; secrets not bundled; paths and updates work as documented.

### [P15-T04] Define release/update and rollback procedure
- **Goal:** Make GitHub releases predictable and not destructive to local data.
- **Prerequisites:** P15-T01/T02; optional P15-T03.
- **Deliverables:** Release/update procedure.
- **Acceptance:** User can distinguish code update from data migration; local secrets/data preserved; no false restore promise.

### [P15-T05] Publish release evidence and close milestone
- **Goal:** Only declare completed work supported by evidence.
- **Prerequisites:** P15-T01–T04.
- **Deliverables:** Release checklist, status board and evidence manifest.
- **Acceptance:** Every claimed complete feature has evidence; unsupported providers/features remain marked unsupported; user receives clear release notes.

## Phase rule
Complete tasks in listed order. If a prerequisite or source artifact is absent, mark the affected task BLOCKED and do not pretend its acceptance tests passed. The phase is done only when every required task is verified and the exit gate has evidence.
