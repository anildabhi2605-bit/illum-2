# P05 — Provider interface and first tested adapter

**Phase intent:** Build routing abstraction and one verified real adapter before skills depend on it.

**Exit gate:** Mocked tests and a configured smoke test confirm safe request, normalized errors, capability metadata and response validation.

## Tasks (strict order)

### [P05-T01] Define provider adapter interface and mock
- **Goal:** Define a uniform request/response/error contract before real provider integration.
- **Prerequisites:** P02/P03 complete.
- **Deliverables:** Provider interface and mock implementation.
- **Acceptance:** Skills cannot access provider SDK directly; mock covers success/invalid schema/rate limit/timeout/auth/model-not-found.

### [P05-T02] Implement the first real provider adapter
- **Goal:** Connect one provider through the shared interface and verify actual capability.
- **Prerequisites:** P05-T01; P00-T04 provider decision; valid credential/access.
- **Deliverables:** One working adapter plus test report.
- **Acceptance:** Valid real request works; invalid key and rate limits handled; model tagged Supported only for tested operations.

### [P05-T03] Implement model catalog and capability metadata
- **Goal:** Expose models with honest source/date/known capabilities.
- **Prerequisites:** P05-T02.
- **Deliverables:** Model catalog service and provenance metadata.
- **Acceptance:** Catalog source and last checked time shown; account/region availability not inferred from catalog alone.

### [P05-T04] Implement project-preferred routing and user-approved fallback
- **Goal:** Enforce preference and explicit alternative model consent.
- **Prerequisites:** P05-T01–T03.
- **Deliverables:** Routing policy, consent dialog and audit field.
- **Acceptance:** No silent switch; no provider from another project accidentally selected; explicit denial stops fallback.

### [P05-T05] Validate provider responses and classify retries
- **Goal:** Prevent malformed results and unsafe retry loops.
- **Prerequisites:** P05-T01–T04.
- **Deliverables:** Response validation and retry policy service.
- **Acceptance:** Schema-invalid output is not saved; retry count bounded; non-transient errors stop.

### [P05-T06] Run provider adapter acceptance suite
- **Goal:** Prove first provider works end-to-end under the common contract.
- **Prerequisites:** P05-T01–T05.
- **Deliverables:** Provider support evidence entry.
- **Acceptance:** Support label limited to tested operations/model; limitations explicit.

## Phase rule
Complete tasks in listed order. If a prerequisite or source artifact is absent, mark the affected task BLOCKED and do not pretend its acceptance tests passed. The phase is done only when every required task is verified and the exit gate has evidence.
