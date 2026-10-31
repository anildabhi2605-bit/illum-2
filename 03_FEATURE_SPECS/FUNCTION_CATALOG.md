# Function Catalog — What the App Must Do

This is a functional inventory, not actual Python function names. Implementation names can be selected in code while preserving behavior. Every function is project-scoped where project data is involved and test-covered before completion.

## Application/runtime functions

| Function area | Required behavior | Phase |
|---|---|---|
| Launch and shutdown | Load config, validate runtime, run migrations as decided, bind localhost, shut down cleanly | P01/P02/P03 |
| Health/status | Report app, database, provider and connector readiness truthfully | P01/P05/P14 |
| Config loading | Load `.env`, validate non-secret settings, report missing keys without values | P02 |
| Key add/remove | Support Notepad edit → save → restart; mask key state; distinguish local removal from provider revocation | P02 |
| Local data paths | Resolve data/export/log/temp directories safely; prevent path traversal | P03 |

## Project functions

| Function area | Required behavior | Phase |
|---|---|---|
| Create project | Generate unique ID; save required settings; enforce project cap | P04 |
| List/open project | Show accurate status and restore settings | P04 |
| Update settings | Validate ratio/duration/language/model and invalidate dependents | P04/P08 |
| Four-project limit | At four, name oldest and prompt: "You already have 4 projects. Do you want to delete the oldest project and create this new project?"; cancel/NO retains four; confirmed replacement safe/recoverable | P04/P13 |
| Project isolation | Scope every read/write/job/export to authorized project ID | P03/P13 |

## Source and analysis functions

| Function area | Required behavior | Phase |
|---|---|---|
| Save/edit/clear source | Preserve title/type/URL/content and unsaved state | P07 |
| Retrieve source URL | Read supported content when possible; accurately distinguish inaccessible URLs/snippets | P07 |
| Validate source | Block generation if content absent, unsaved or unreadable | P07 |
| Version source | Increment source version on meaningful changes and preserve source version history | P07 |
| Analyze source | Create once per source version; reuse while valid | P08/P09 |
| Analyze script | Create once per current script version; reuse while valid | P08/P09/P10/P12 |
| Invalidate dependencies | Mark stale analyses, approval and outputs when inputs/settings change | P08 |

## Script and four skill functions

| Function area | Required behavior | Phase |
|---|---|---|
| Generate candidate script | Run exact Skill A contract on saved validated source/settings | P09 |
| Validate script | Check required structure, part count, language, duration and fields | P09 |
| Replace latest script | Preserve current on failed candidate; replace only after validation; no permanent script history | P08/P09 |
| Approve script | Bind approval to current script hash/version and relevant settings | P08/P09 |
| Generate video prompts | Current approved script; valid Script Analysis; one prompt per part; validation report | P10 |
| Generate thumbnail prompt | Entire current approved script; exactly one complete prompt; correct ratio/language | P11 |
| Generate SEO | Title, description, keywords, hashtags and separate comma-separated tags; always Roman Hindi | P12 |
| Output freshness | Show current/stale status and keep previous valid output until candidate passes | P08–P12 |

## Shared AI execution functions

| Function area | Required behavior | Phase |
|---|---|---|
| Adapter registry | Only implemented/tested adapters marked Supported | P05 |
| Connection/model validation | Check credentials, access, availability and capabilities where known | P05 |
| Route request | Project-preferred model first; no unapproved per-skill routing complexity | P05 |
| Alternative consent | Ask explicit permission before trying alternative | P05 |
| Error normalization | Separate auth, access, billing, rate-limit, timeout, network, missing-model and schema errors | P05 |
| Schema validation | Reject malformed response before save/return | P05/P09–P14 |
| Job lifecycle | Queued/Running/Validating/Completed or Failed/Cancelled | P06 |
| Duplicate prevention | Avoid duplicate active generation for same operation | P06 |
| Retry/cancel | Bounded safe retry; no blind retries of non-transient failures | P06 |
| Usage/history | Record actual exposed usage; metadata only; strictly zero raw prompts/payloads; max 100 records/project FIFO (DEC-018) | P06 |

## Export, security and maintenance functions

| Function area | Required behavior | Phase |
|---|---|---|
| Project ZIP export | Include required project artifacts/metadata; exclude secrets; data-only, no restore | P13 |
| Project deletion | Confirm, cascade delete linked rows, execution history (DEC-018) and temp files; preserve shared .env credentials | P13 |
| Retention cleanup | Retain latest 100 history records/project via FIFO; cascade on project delete; never delete/modify .env (DEC-018) | P13 |
| Diagnostics | Sanitized errors and useful local troubleshooting without secret/source leakage | P06/P13/P15 |
| Clean installation/update | Reproducible setup, dependency update, migrations and smoke tests | P15 |
| Optional packaging | Build/test OS-specific package only after source-based workflow passes | P15 |

## Module E — Idea Research & Discovery functions (optional)

| Function area | Required behavior | Phase |
|---|---|---|
| Configure research run | Region, time window, niche/topic, language and enabled connectors | P14 |
| Connector readiness | Show configured/available/restricted/rate-limited/failed status | P14 |
| Search and collect | Query Trends, News/web, keyword and approved social adapters as configured | P14 |
| Normalize and deduplicate | Normalize timestamps, URLs and topic aliases; remove duplicate/repost inflation | P14 |
| Rank candidates | Return up to four evidence-backed topics; explain factors; separate trend from evidence confidence | P14 |
| Research dossier | Create sourced timeline, claims, context, keyword signals, conflicts and references | P14 |
| Import to Source Panel | Require explicit user action, then save and validate via existing source flow | P14 |

## Global invariants across functions

- All project content operations are scoped by `project_id`.
- No source generation without a saved, validated source.
- No downstream skill execution without matching current script approval.
- No silent AI model fallback.
- No stale output presented as current.
- No secrets in logs, Git, user exports or project data.
- No feature marked complete without acceptance evidence.
