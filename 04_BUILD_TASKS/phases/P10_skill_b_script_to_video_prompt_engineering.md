# P10 — Skill B — Script-to-Video Prompt Engineering

**Phase intent:** Add the second protected skill only after Skill A and approval gates work.

**Exit gate:** Each current approved part yields required prompt/report; invalid or stale scripts are blocked.

## Tasks (strict order)

### [P10-T01] Wire Skill B input and approval gate
- **Goal:** Bind original Skill B contract to current approved script/settings.
- **Prerequisites:** P09 complete; P08 approved gate.
- **Deliverables:** Skill B use case and contract mapping.
- **Acceptance:** Unapproved/stale request rejected; current approved input mapped exactly.

### [P10-T02] Generate per-part video prompts
- **Goal:** Create prompts reflecting each part’s action and constraints.
- **Prerequisites:** P10-T01; P05/P06.
- **Deliverables:** Per-part prompt generation service.
- **Acceptance:** One prompt per required part, grounded in script and settings, correct durations.

### [P10-T03] Validate and persist Skill B outputs
- **Goal:** Apply schema, ratio, language and freshness checks before saving.
- **Prerequisites:** P10-T02; P08 invalidation.
- **Deliverables:** Skill B output repository/invalidation hooks.
- **Acceptance:** Invalid outputs not marked current; output provenance points to script hash/settings.

### [P10-T04] Run Skill B acceptance suite
- **Goal:** Prove Skill B works through UI and backend.
- **Prerequisites:** P10-T01–T03.
- **Deliverables:** Skill B acceptance report.
- **Acceptance:** All expected prompts and validation report pass; no silent generation without approval.

## Phase rule
Complete tasks in listed order. If a prerequisite or source artifact is absent, mark the affected task BLOCKED and do not pretend its acceptance tests passed. The phase is done only when every required task is verified and the exit gate has evidence.
