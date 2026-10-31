# Product Rules and Invariants — Source of Truth

Use the approved original source plan for exact requirements. This file consolidates the rules that implementation must never violate.

## 1. Four protected skills

1. **A — Story-to-Script:** Source-grounded script; confirm source content is saved and validated; no unsupported facts; project language controls script and VO; Hindi content uses Devanagari.
2. **B — Script-to-Video Prompt Engineering:** Produces prompts, not video files. Uses current approved script and valid Script Analysis; respects aspect ratio, language, continuity, and part duration.
3. **C — Thumbnail Intelligence:** Produces exactly one complete image-generation prompt based on the entire current approved script; does not generate the image itself.
4. **D — YouTube SEO:** Title, description, keywords, hashtags and separate comma-separated tags. SEO is always Roman Hindi in Latin alphabet. Do not fabricate search volume or guarantee ranking.

Original skill prompts must be imported from their authoritative source before any skill is declared contract-complete. A summary is not an adequate substitute.

## 2. Projects and isolation

- Every project has unique `project_id` and isolated project data.
- Maximum four active saved projects (DEC-019).
- When creating a fifth project, prompt the user: "You already have 4 projects. Do you want to delete the oldest project and create this new project?", identifying the oldest project by `created_at` timestamp and project name.
- If the user selects NO or cancels, retain all four existing projects and do not create the new project.
- On explicit YES confirmation, deletion must be atomic/recoverable; never lose old project if new-project operation fails. Never automatically delete any project without explicit confirmation.
- Manual deletion requires confirmation and is permanent in-app; no restore feature is approved.
- Shared credentials remain when a project is deleted unless explicitly project-scoped.

## 3. Aspect ratio, language, and duration

- `9:16`: target 1080x1920; only approved total durations 24/32/40/48/56 seconds; 3/4/5/6/7 parts; every part is 8 seconds; structure Hook + story parts + Ending. Do not add 60 seconds.
- `16:9`: target 1920x1080; total minimum 180 seconds; each part must be >0 and <=8 seconds; match total exactly where possible.
- Hindi: script/voiceover and thumbnail text use Devanagari.
- English: script/voiceover and thumbnail text use English.
- SEO always Roman Hindi.
- Reopen project restores settings. New project asks again. Skills cannot silently override settings.

## 4. Source and script lifecycle

- Source has title, optional URL, saved content, source type/status, `source_version` and analysis status.
- Saved URL does not imply fetched/read content.
- If a URL cannot be read, report why and offer pasted content.
- Script generation disabled until source is saved and validated.
- Meaningful source edits create a new source version and stale dependent outputs.
- Generate source analysis once per source version and reuse while valid.
- Generate script analysis once per current script version and reuse while valid.
- Only latest script is stored. Preserve prior saved script until a replacement candidate passes validation; then overwrite.
- Every script edit/regeneration needs a new approval tied to current exact script version/hash and relevant settings.
- Downstream skills are disabled without current approval.

## 5. Model manager

- Routes requests; does not replace skill logic/contracts.
- A provider/model is Supported only after adapter implementation and tests.
- Unknown model/cost/quota/capability metadata remains Unknown; do not guess.
- Preferred model failure must be shown to user; alternative model requires explicit user permission. No silent switch.
- Respect rate limits; bounded retries only for appropriate transient errors.
- Do not blindly retry invalid keys, access/region/plan errors, billing errors or model-not-found.
- Validate response schema before returning to a skill.
- Do not log secrets or unnecessary prompt content.

## 6. Jobs and usage

- Job states: `Queued → Running → Validating → Completed`, or `Failed` / `Cancelled`.
- Show truthful progress, prevent duplicate jobs, persist state across reloads where architecture supports it, explain failures, and preserve old outputs until new output validates.
- Record tokens/usage/cost/quota only when exposed reliably. Use `Estimate` or `Unknown` when appropriate.
- Execution history retention is capped strictly at the latest 100 execution history records per project with automatic FIFO pruning (DEC-018).
- Execution history stores operational metadata only: project ID, job ID, skill ID, provider/model, timestamps, duration/latency, status, attempt count, sanitized error code/type, token usage metrics, fallback reason and user consent records.
- Strict negative constraint: never persist raw prompts, raw source text, or raw LLM request/response payloads in execution history (DEC-018).

## 7. Security, export, retention

- Never expose secrets in client bundles, URLs, logs, exported ZIPs or project records.
- Local-mode `.env` is plain text; secure file access, `.gitignore`, redaction, and clear warnings are required. It is not equivalent to encrypted server-side storage.
- Export is data-only; no restore/import capability is approved unless separately changed in the decision register.
- Export ZIP includes source, latest script, approval status, video prompts, thumbnail prompt, SEO, settings and JSON metadata; excludes secrets.
- Deleting a project cascades to delete all linked project data, project-specific execution history records (DEC-018), cache and temporary files.
- Environmental safety invariant: Project deletion, data cleanup, or execution history retention pruning must NEVER delete or modify the shared `.env` file under any circumstance (DEC-018).

## 8. Idea Research — requested optional addition

- Module E is optional and is a pre-source route, not a replacement for direct source entry.
- It may discover and rank up to four topics from configured, actually available sources; never fabricate coverage or results.
- Trend score and factual confidence are separate concepts.
- Clicked topic opens a detailed evidence-backed dossier; report can be reviewed and optionally imported into the existing Source Panel.
- Connectors (Google Trends/PyTrends, Keyword Tool, News, web, X, Reddit) are independently configured and report status/limitations. No source is claimed available unless tested.
- PyTrends is unofficial/archived in the prior research discussion; treat as experimental, optional and replaceable, not critical infrastructure.
- Do not claim complete “whole internet” coverage. Scope results by region, window, connectors and retrieval time.

## 9. Governance

- No unapproved behavior, missing requirements or changes to a skill contract.
- Conflicts or unsupported technology must be logged as blocker and brought to user; do not guess.
- A feature is not complete without acceptance evidence.
