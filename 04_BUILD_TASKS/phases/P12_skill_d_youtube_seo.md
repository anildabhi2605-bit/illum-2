# P12 — Skill D — YouTube SEO

**Phase intent:** Add structured project-aware SEO output.

**Exit gate:** Roman Hindi and all required fields are validated and stale context is caught.

## Tasks (strict order)

### [P12-T01] Define SEO result schema and Roman Hindi validation
- **Goal:** Create strict output contract with separate comma-separated tags.
- **Prerequisites:** P09/P08 complete; original Skill D imported.
- **Deliverables:** SEO schema and validators.
- **Acceptance:** Required fields present; Roman Hindi policy applied; schema tests cover English project.

### [P12-T02] Generate project-aware SEO package
- **Goal:** Use current source/script and valid saved analyses.
- **Prerequisites:** P12-T01; provider/job manager; approval policy.
- **Deliverables:** SEO generation use case.
- **Acceptance:** Output follows current source/script and is Roman Hindi; no unsupported claims.

### [P12-T03] Validate, save and invalidate SEO output
- **Goal:** Store valid SEO per project and mark it stale when inputs change.
- **Prerequisites:** P12-T02; P08 invalidation.
- **Deliverables:** SEO package persistence/invalidation.
- **Acceptance:** Only validated package current; stale state correct; no cross-project leakage.

### [P12-T04] Run Skill D acceptance suite
- **Goal:** Verify SEO contract in the app end-to-end.
- **Prerequisites:** P12-T01–T03.
- **Deliverables:** Skill D acceptance evidence.
- **Acceptance:** All tests pass and provenance is recorded.

## Phase rule
Complete tasks in listed order. If a prerequisite or source artifact is absent, mark the affected task BLOCKED and do not pretend its acceptance tests passed. The phase is done only when every required task is verified and the exit gate has evidence.
