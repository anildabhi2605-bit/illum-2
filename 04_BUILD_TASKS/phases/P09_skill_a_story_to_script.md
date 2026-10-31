# P09 — Skill A — Story-to-Script

**Phase intent:** Implement the first protected skill end-to-end.

**Exit gate:** Original contract tests pass; candidate scripts validate; latest-only replacement and reapproval work.

## Tasks (strict order)

### [P09-T01] Bind Skill A original contract to use case
- **Goal:** Connect protected original Story-to-Script prompt without changing its logic.
- **Prerequisites:** P00-T01 complete; P05/P06/P07/P08 exit gates passed.
- **Deliverables:** Skill A orchestrator with contract provenance.
- **Acceptance:** Exact original contract is used and versioned; request/response mapping does not remove requirements.

### [P09-T02] Generate and reuse Source Analysis
- **Goal:** Implement once-per-source-version analysis and provenance.
- **Prerequisites:** P09-T01; P08-T01.
- **Deliverables:** Source Analysis flow.
- **Acceptance:** Cache hit reuses; version mismatch regenerates; outputs trace to source.

### [P09-T03] Implement fact-grounded script generation
- **Goal:** Generate script according to exact source, settings and original prompt.
- **Prerequisites:** P09-T01/T02; P05/P06.
- **Deliverables:** Script candidate generator.
- **Acceptance:** No unsupported facts by contract tests; output language and part fields correct; internal analysis not mislabeled as script.

### [P09-T04] Implement script/duration validation and targeted correction
- **Goal:** Reject invalid script structure and correct only failed constraints.
- **Prerequisites:** P09-T03; P04 duration service.
- **Deliverables:** Script validator/correction orchestration.
- **Acceptance:** No invalid candidate saved as current; no silent duration changes; corrections are targeted and evidence logged.

### [P09-T05] Complete Skill A review/approval end-to-end test
- **Goal:** Verify source→script→candidate→saved latest→approval lifecycle.
- **Prerequisites:** P09-T01–T04 and P08 exit.
- **Deliverables:** Skill A acceptance evidence.
- **Acceptance:** All core script workflow and approval invariants pass.

## Phase rule
Complete tasks in listed order. If a prerequisite or source artifact is absent, mark the affected task BLOCKED and do not pretend its acceptance tests passed. The phase is done only when every required task is verified and the exit gate has evidence.
