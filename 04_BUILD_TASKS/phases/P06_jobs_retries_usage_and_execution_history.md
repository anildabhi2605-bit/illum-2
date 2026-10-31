# P06 — Jobs, retries, usage and execution history

**Phase intent:** Build the shared execution control plane before source/skill workflows.

**Exit gate:** Jobs transition honestly, duplicates are prevented, safe retries are bounded, history is sanitized and usage labels are truthful.

## Tasks (strict order)

### [P06-T01] Implement job state machine and progress
- **Goal:** Create central lifecycle for generation jobs.
- **Prerequisites:** P05 interface; P03 job model.
- **Deliverables:** Job service and status model.
- **Acceptance:** Invalid transitions rejected; reload reflects actual status; no fake percentage.

### [P06-T02] Prevent duplicate jobs and handle idempotency
- **Goal:** Prevent repeated Generate clicks from causing duplicate paid work.
- **Prerequisites:** P06-T01; P03 constraints.
- **Deliverables:** Idempotency/duplicate prevention service.
- **Acceptance:** Repeated clicks or requests do not create duplicate active jobs for same operation; distinct input versions may start new jobs.

### [P06-T03] Implement safe retries and cancellation handling
- **Goal:** Ensure retry uses current validated input and respects error category.
- **Prerequisites:** P06-T01/T02; P05-T05.
- **Deliverables:** Retry/cancel use cases.
- **Acceptance:** Retry bounded, truthful and safe; cancellation state not claimed before confirmed; old output preserved.

### [P06-T04] Track execution history and usage honestly
- **Goal:** Persist execution metadata without secrets, invented costs, or raw payloads; cap history at 100 records per project with FIFO cleanup (DEC-018).
- **Prerequisites:** P06-T01; P05 adapter response.
- **Deliverables:** History repository/service, FIFO retention pruner, and data labels.
- **Acceptance:** No secret leakage; unavailable cost/quota labeled Unknown/Estimate; history capped at 100 per project; zero raw payloads; cascade delete on project deletion; `.env` untouched.

### [P06-T05] Build jobs/history UI and failure messages
- **Goal:** Surface actual states and actionable errors.
- **Prerequisites:** P06-T01–T04.
- **Deliverables:** Jobs/history UI.
- **Acceptance:** UI matches DB state and error type; no fake progress; duplicate job state visible.

## Phase rule
Complete tasks in listed order. If a prerequisite or source artifact is absent, mark the affected task BLOCKED and do not pretend its acceptance tests passed. The phase is done only when every required task is verified and the exit gate has evidence.
