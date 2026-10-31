# UI/UX Specification — Local AI Studio

This document defines screens and interaction requirements, not a finalized visual skin. The exact UI framework is a Phase P00 decision.

## Global navigation

1. Dashboard / Projects.
2. Project Overview.
3. Source & Research (manual source route always available; Idea Research optional).
4. Script Review & Approval.
5. Video Prompts.
6. Thumbnail Prompt.
7. YouTube SEO.
8. AI Providers & Models (global local config; masked secret status).
9. Jobs / Execution History / Usage.
10. Export / Delete / App Settings.

## Screen: Project Dashboard

- Show active projects, created/updated time, key settings and latest job/status.
- At most four active saved projects (DEC-019).
- “New Project” opens settings creation flow.
- If four projects already exist, show the oldest `created_at` project name and prompt: "You already have 4 projects. Do you want to delete the oldest project and create this new project?". Cancel/NO keeps all four; explicit YES confirm follows safe atomic/recoverable flow.
- Do not label a project output complete if only generation was requested; show the actual state.

## Screen: New Project

Required fields: project name/title, ratio (`9:16` or `16:9`), duration under the respective approved rules, content language (Hindi/English), project preferred provider/model from tested available choices where possible.
- Show portrait/landscape target dimensions.
- Inline validation; do not auto-correct to unapproved durations silently.
- Save settings before opening Source Adding Panel.

## Screen: Source Adding Panel

Fields: Source Title, optional Source URL, Main Source Content, source type. Actions: Save Source, Edit Source, Clear Unsaved Text. Status labels: Unsaved, Saved, Changes Not Saved, Validated, Failed/Unreadable.
- Clearly separate `URL saved` from `URL content retrieved and validated`.
- When URL retrieval fails, explain reason and allow pasted content.
- Keep Generate Script disabled until source is saved and validated.
- If source came from Idea Research, show its report/source references and allow user editing before save/validation.

## Screen: Script Review

- Show current script, part-by-part breakdown, validation result, duration count and language checks.
- Actions: approve, edit, regenerate, cancel. A replacement is a candidate until it passes validation.
- Approval badge/state must reference the exact current script hash/version and project settings.
- On changed script or dependent setting, revoke current approval and disable B/C/D.

## Screen: Skill outputs

- Video Prompts: one prompt per script part, part index/duration and validation state.
- Thumbnail: one complete prompt based on full approved script.
- SEO: title, description, keywords, hashtags and separately comma-separated tags; all SEO output Roman Hindi.
- Show input version/hash, generated time, provider/model and freshness state as useful metadata.
- Keep previous valid output until a replacement passes validation.

## Screen: AI Providers & Models

- Show configured providers, connection test status, supported models and known capability metadata.
- Add/update/remove key workflow; mask key after save. For the requested local developer workflow, user may edit `.env` in Notepad and restart app.
- Explain that `.env` is plaintext on disk and must never be committed.
- A provider or model should not show “Supported” until adapter and tests are complete.
- Alternative model approval must be explicit and tied to a specific job/request.

## Screen: Idea Research (optional Module E)

Controls: region/geography, time window, topic/niche filter, language/query settings, enabled connectors. Show per-connector status and actual scan coverage.
- Result list contains up to four topics only when evidence supports them.
- Each card includes ranking rationale, trend score, evidence confidence, recency/retrieval timestamp, key sources and connector coverage.
- Clicking opens a detailed research dossier; user must explicitly choose “Import as Main Source” to populate Source Panel.

## Accessibility and state rules

- All controls need visible labels, keyboard focus and readable error messages.
- Loading progress must report actual job state; never fake percentages.
- Every destructive action requires confirmation.
- No secret values in screenshots, logs, HTML, client state dumps or exports.
- UI must reflect authoritative domain state and not independently decide invalidation or approval.
