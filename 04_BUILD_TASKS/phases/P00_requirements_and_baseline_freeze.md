# P00 — Requirements and baseline freeze

**Phase intent:** No code work until the authoritative inputs, requested amendments and test baseline are clarified.

**Exit gate:** P00 is complete when original A-D prompt contracts and original acceptance matrix are imported (or explicitly logged as a blocker), requested local-first and Module E changes are recorded, stack/provider decisions are explicit, and acceptance scope is frozen.

## Tasks (strict order)

### [P00-T01] Import authoritative product artifacts
- **Goal:** Collect the exact original A-D skill prompt contracts and the referenced original acceptance matrix; summaries cannot replace these.
- **Prerequisites:** None. This is the first task.
- **Deliverables:** Versioned contract files for A-D; authoritative acceptance matrix; artifact manifest; missing-items report.
- **Acceptance:** No skill is marked contract-ready without exact prompt; original matrix is distinguishable from proposed matrix; no content silently recreated from memory.

### [P00-T02] Reconcile requested amendments into baseline
- **Goal:** Record local Python/.env deployment and optional Idea Research as explicit amendments without altering core skill contracts.
- **Prerequisites:** P00-T01 artifact inventory available.
- **Deliverables:** Versioned amended requirements and updated decision register/changelog.
- **Acceptance:** Every changed behavior has change ID, rationale, impacted docs and approval status; old baseline preserved verbatim.

### [P00-T03] Choose and record the technology stack
- **Goal:** Select the smallest stack that can satisfy local UI, persistence, testing, provider routing and optional research needs.
- **Prerequisites:** P00-T02.
- **Deliverables:** Architecture decision record with versioned stack and rationale.
- **Acceptance:** One coherent stack is selected; trade-offs documented; no duplicate frameworks; unknown platform constraints identified.

### [P00-T04] Freeze connector, credentials and retention boundaries
- **Goal:** Define provider and research connector policy, secret storage boundary and data retention before connecting external services.
- **Prerequisites:** P00-T02; P00-T03 where stack needed.
- **Deliverables:** Security/connector decision record; retention policy; initial provider/capability checklist.
- **Acceptance:** No connector called supported without tests; no secrets exported/logged; local mode is not falsely described as encrypted.

### [P00-T05] Baseline acceptance tests and phase gates
- **Goal:** Create traceability from every invariant to a measurable test and phase exit gate.
- **Prerequisites:** P00-T01 through P00-T04.
- **Deliverables:** Requirement-to-test traceability matrix; release criteria; P00 sign-off.
- **Acceptance:** No critical invariant lacks a test; missing tests are logged; phase order and status vocabulary are clear.

## Phase rule
Complete tasks in listed order. If a prerequisite or source artifact is absent, mark the affected task BLOCKED and do not pretend its acceptance tests passed. The phase is done only when every required task is verified and the exit gate has evidence.
