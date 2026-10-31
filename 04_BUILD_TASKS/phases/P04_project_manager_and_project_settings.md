# P04 — Project manager and project settings

**Phase intent:** Build project creation/open/list/settings and exact input rules before skill logic.

**Exit gate:** Project creation, restore, setting validation and four-project behavior pass tests (DEC-019).

## Tasks (strict order)

### [P04-T01] Implement project create/list/open lifecycle
- **Goal:** Build project selection and persistence before detailed feature screens.
- **Prerequisites:** P03 complete.
- **Deliverables:** Project manager use cases and dashboard.
- **Acceptance:** Project persists/reopens; project IDs are never reused; list reflects true DB state.

### [P04-T02] Build settings form and ratio/language rules
- **Goal:** Implement project settings with exact allowed choices.
- **Prerequisites:** P04-T01; P03-T01.
- **Deliverables:** Settings UI and validation service.
- **Acceptance:** No silent setting overrides; saved values persist; Hindi/English mapping is visible and correct.

### [P04-T03] Implement exact duration/part calculator
- **Goal:** Centralize duration math and boundary validation.
- **Prerequisites:** P04-T02.
- **Deliverables:** Duration/part-plan domain service.
- **Acceptance:** 24/32/40/48/56 rules exact; 60 not allowed; landscape boundaries and total sum pass.

### [P04-T04] Enforce four-project active limit transactionally
- **Goal:** Implement project-limit guard and oldest-project confirmation UX.
- **Prerequisites:** P04-T01; P03-T02.
- **Deliverables:** Project-limit policy and confirmation flow.
- **Acceptance:** Cancel leaves four; confirmed path cannot delete before replacement operation is safe; concurrent create cannot exceed limit.

### [P04-T05] Test project/settings UX states
- **Goal:** Verify validation, errors and recovery from UI.
- **Prerequisites:** P04-T01–T04.
- **Deliverables:** UI test evidence and updated screenshots if useful.
- **Acceptance:** Displayed UI matches domain state; no stale settings or misleading project count.

## Phase rule
Complete tasks in listed order. If a prerequisite or source artifact is absent, mark the affected task BLOCKED and do not pretend its acceptance tests passed. The phase is done only when every required task is verified and the exit gate has evidence.
