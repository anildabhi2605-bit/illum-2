# P07 — Source Adding Panel and validation

**Phase intent:** Build source persistence/validation before script generation.

**Exit gate:** Only saved validated content unlocks Script A; URL failures are represented accurately; source versions are preserved.

## Tasks (strict order)

### [P07-T01] Implement source-version repository/model
- **Goal:** Persist source versions and metadata under a project.
- **Prerequisites:** P03/P04 complete.
- **Deliverables:** Source service and storage model.
- **Acceptance:** Versions monotonic per source; version records isolated per project; URL presence not read status.

### [P07-T02] Build Source Adding Panel UI and status actions
- **Goal:** Implement manual source path fully before research import.
- **Prerequisites:** P07-T01; UI spec.
- **Deliverables:** Source Panel.
- **Acceptance:** User can save/edit/clear and see correct statuses; direct-source workflow always available.

### [P07-T03] Implement source readability/content validation
- **Goal:** Confirm actual content is usable; handle URLs honestly.
- **Prerequisites:** P07-T01/T02; HTTP reader capability decision.
- **Deliverables:** Source validation service and readable error mapping.
- **Acceptance:** Script cannot run without saved validated content; URL fetch failure is clear and never disguised as success.

### [P07-T04] Connect source edits to invalidation hooks
- **Goal:** Ensure version change marks analyses and outputs stale.
- **Prerequisites:** P07-T01/T03; P08 may provide shared invalidation contract.
- **Deliverables:** Source change integration event.
- **Acceptance:** One authoritative invalidation route; no stale output presented as current.

### [P07-T05] Verify source workflow acceptance
- **Goal:** Prove source input is stable before Skill A.
- **Prerequisites:** P07-T01–T04.
- **Deliverables:** Source workflow test evidence.
- **Acceptance:** All source gate checks pass from UI and direct backend call.

## Phase rule
Complete tasks in listed order. If a prerequisite or source artifact is absent, mark the affected task BLOCKED and do not pretend its acceptance tests passed. The phase is done only when every required task is verified and the exit gate has evidence.
