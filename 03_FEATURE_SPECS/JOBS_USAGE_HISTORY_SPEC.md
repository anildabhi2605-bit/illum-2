# Jobs, Progress, Retry, Usage and Execution History

## Job lifecycle

`Queued → Running → Validating → Completed`, or `Failed` / `Cancelled`.

Progress must reflect real state. Do not invent percentage. Prevent duplicate clicks/jobs for the same operation via UI and backend idempotency/active-job checks. Persist job state across reload where supported by architecture.

## Retry rules

- Show understandable failure and safe retry action.
- Validate current inputs/settings before retry.
- Retry only appropriate transient errors, bounded by configured maximum.
- No blind retry for invalid key, access/region/plan, billing or model-not-found.
- A timeout may happen after provider completion; use request/job identifiers/idempotency where possible to avoid duplicate expensive work.
- Alternative model is a separate explicit permission path.
- Keep old saved output until a new candidate validates.

## Execution history fields and retention policy (DEC-018)

- **Retention Cap & FIFO Pruning:** Retain strictly the latest 100 execution history records per project. When a 101st execution record is generated, the oldest record for that project is automatically pruned via FIFO cleanup.
- **Metadata Only:** Fields stored include project ID, skill ID/module ID, provider/model, job ID, start/end timestamps, duration/latency in milliseconds, status (`QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`), attempt count, normalized and sanitized error code/type, usage/token counts (prompt/completion/total) when available, actual cost only when reliably returned, fallback reason and explicit user permission records.
- **Strict Prohibition on Raw Content:** Never log API keys. Strictly do not persist raw prompts, raw source text, or raw LLM request/response payloads in execution history or database tables.
- **Cascade Cleanup on Project Deletion:** All project-specific execution history records are automatically deleted when the associated project is deleted.
- **Environmental Safety Invariant:** Execution history retention cleanup and project deletion operations must NEVER delete or modify the shared `.env` file under any circumstance.

## UI

Job list/detail shows actual current state and timestamp; errors identify user action; retry is disabled when input invalid or operation already running. Usage labels use actual / estimate / unknown honestly.
