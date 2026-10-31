# Project, Source, Script, Versioning and Approval Specification

## Project creation

1. New Project.
2. Select aspect ratio.
3. Select duration constrained by ratio.
4. Select content language.
5. Select preferred supported provider/model from actual configured models.
6. Save settings and create unique project ID.
7. Open Source Adding Panel.

Reopening an existing project restores its saved settings. New projects ask again.

## Source panel contract

Fields: source title, source type, optional URL, main content. Actions: save, edit, clear unsaved text. Statuses: unsaved, saved, changes not saved, validated, failed/unreadable.
- URL presence alone does not prove source retrieval.
- Validate text is usable before script generation.
- If URL cannot be read, explain and request pasted content.
- Meaningful change increments source version; preserve source version history.

## Analysis reuse

- Source analysis: once per source version; reuse while valid.
- Script analysis: once per current script version; reuse while valid.
- Skill B reuses valid Script Analysis.
- Skill D reuses valid Source Analysis and Script Analysis.
- Reanalyze only if missing, stale, underlying input changes, or explicit user request.

## Latest script and candidate replacement

- Store latest script only; no permanent script history table.
- Edit/regeneration creates a candidate, validated before replacing current script.
- If candidate fails, prior saved script remains.
- If candidate passes, replace current script and invalidate approval/dependent outputs.
- Require new approval after every edit/regeneration.

## Approval invariant

Approval is valid only if approved script hash/version and relevant project settings match current values. Skill B/C/D generation endpoints and UI actions must independently enforce approval. Hiding buttons in the UI is not sufficient.

## Stale rules

Source change → source analysis stale and dependent generated outputs stale as applicable.
Script change → script analysis, approval, video prompts, thumbnail prompt and SEO stale as applicable.
Ratio/language/duration change → revalidate or regenerate dependent outputs and invalidate approval if the setting is in the approval hash.
