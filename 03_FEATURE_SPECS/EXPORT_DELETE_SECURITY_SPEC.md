# Export, Deletion, Security and Retention Specification

## Data-only export

ZIP must include current source/source metadata, latest script, approval status, video prompts, thumbnail prompt, SEO package, project settings and JSON metadata. If Module E has been implemented and the research export amendment is accepted, include selected research dossier and relevant evidence metadata. Never include API keys, `.env`, secret-store files or credentials.

No project restore/import feature is approved. Do not build restore without a separately recorded change.

## Project deletion

- Manual deletion requires explicit confirmation.
- Fifth-project flow names the oldest project and asks: "You already have 4 projects. Do you want to delete the oldest project and create this new project?" before deleting (DEC-019).
- Perform deletion in a transaction/recoverable operation so failure cannot cause accidental loss.
- Delete linked DB records, project-specific execution history records (DEC-018), project-local files, caches, temp files and research artifacts.
- Preserve shared provider credentials: never delete or modify the shared `.env` file under any circumstance during project deletion, history cleanup, or database maintenance (DEC-018).
- Report actual result; no false success if cleanup partially fails.

## Local-mode security

- `.env` ignored by Git; example file contains placeholders only.
- Avoid secrets in logs, errors, crash reports, URLs, exports and source control.
- Mask configured keys in UI; never display full saved key on later reads.
- Limit local server to localhost by default.
- Restrict permissions for local data/secret files where supported.
- Provide key removal instructions and state that local removal does not revoke key remotely.
- Do not call local plaintext `.env` encrypted storage.

## Retention (DEC-018)

- Only store data needed for the app. Temporary files cleaned up after jobs and deletions.
- Execution-history retention is strictly capped at the latest 100 execution history records per project, pruned via FIFO upon the 101st execution record.
- Execution history records store operational metadata only (timestamps, duration/latency, status, attempt count, token usage metrics, model, provider, sanitized error code); strictly do not persist raw prompts, raw source text, or raw LLM request/response payloads.
- Delete project-specific history when that project is deleted.
- Environmental safety invariant: History pruning, project deletion, and local database cleanups must NEVER delete or modify the shared `.env` file.
- Backup recommendations and deletion boundaries must be documented.

## Tests

Inspect zip contents, sentinel-secret scan, project deletion cleanup (asserting deletion of project records and project-specific execution history while verifying shared `.env` remains untouched), 100-record execution history retention FIFO pruning boundary test, metadata-only history verification (asserting absence of raw prompts/payloads), failure-safe deletion, Git ignored files, local bind behavior and log redaction.
