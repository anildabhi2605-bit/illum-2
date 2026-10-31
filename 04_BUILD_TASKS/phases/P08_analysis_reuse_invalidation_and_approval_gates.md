# P08 — Analysis reuse, invalidation and approval gates

**Phase intent:** Build source/script dependency and approval invariants before implementing any downstream skill.

**Exit gate:** Stale state propagates correctly and backend APIs reject unapproved/stale operations.

## Tasks (strict order)

### [P08-T01] Implement reusable analysis cache keyed by inputs
- **Goal:** Reuse analysis only while exact input version remains valid.
- **Prerequisites:** P07 complete; P03 analysis model.
- **Deliverables:** Analysis cache service.
- **Acceptance:** One analysis per valid source/script version under agreed policy; stale/missing triggers reanalysis.

### [P08-T02] Implement dependency invalidation engine
- **Goal:** Centralize stale-state rules for source/script/settings/output.
- **Prerequisites:** P08-T01; P07-T04.
- **Deliverables:** Dependency/invalidation service.
- **Acceptance:** All triggers produce deterministic stale states; no UI-specific duplicate logic.

### [P08-T03] Implement latest-script candidate replacement transaction
- **Goal:** Guarantee failed candidate does not destroy current script.
- **Prerequisites:** P08-T02; script storage schema.
- **Deliverables:** Candidate replacement service.
- **Acceptance:** Old latest preserved on failure; successful output atomically replaces; permanent script-history table absent.

### [P08-T04] Enforce approval hash/settings gate on backend
- **Goal:** Make approval an authorization rule, not merely a UI badge.
- **Prerequisites:** P08-T02/T03.
- **Deliverables:** Approval service and backend guards.
- **Acceptance:** No downstream skill starts without matching current approval; UI bypass cannot circumvent.

### [P08-T05] Build approval and stale-state UI
- **Goal:** Display current version, approval and stale outputs accurately.
- **Prerequisites:** P08-T01–T04.
- **Deliverables:** Review/approval UX.
- **Acceptance:** UI state matches backend; stale approval not visually active; no misleading green completion state.

### [P08-T06] Run version, analysis and approval matrix
- **Goal:** Prove all invalidation combinations before skills.
- **Prerequisites:** P08-T01–T05.
- **Deliverables:** P08 acceptance report.
- **Acceptance:** Every row in invalidation matrix passes.

## Phase rule
Complete tasks in listed order. If a prerequisite or source artifact is absent, mark the affected task BLOCKED and do not pretend its acceptance tests passed. The phase is done only when every required task is verified and the exit gate has evidence.
