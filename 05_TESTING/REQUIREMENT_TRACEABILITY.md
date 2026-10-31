# Requirement-to-Implementation Traceability Matrix & Phase Gates

**Governance Status:** Authoritative Testing Blueprint (Ratified under P00-T05; DEC-005, DEC-018, DEC-019).  
**Baseline Reconciliation:**
- **Total Unique Tests:** 53
- **Approved Baseline Tests:** 52
- **Proposed / Out-of-Baseline Tests:** 1 (`ACC-001A` — tied to `DEC-015`)
- **Primary Runtime:** Python 3.12 (Python 3.11 as conditional fallback per ADR-001)
- **Authoritative Master Plan:** Preserved verbatim in `99_REFERENCE_SOURCE/01_MASTER_PLAN_APPROVED_ORIGINAL.md` (DEC-001).

---

## 1. Comprehensive Requirement-to-Acceptance Test Mapping (53 Tests)

| Test ID | Requirement Area | Primary Spec | Build Task | Measurable Invariant Verified | Governance Status |
|---|---|---|---|---|---|
| **ACC-001** | Python Runtime Environment | Master Plan 1.1; ADR-001 | `P01-T01` | Clean venv creation & dependency installation without compilation errors | `PLANNED` |
| **ACC-001A** | Localhost Network Binding | ADR-001 Sec 4; DEC-015 | `P01-T02` | Server listens strictly on `127.0.0.1`; external LAN requests cannot connect | **`PROPOSED (DEC-015)`** |
| **ACC-002** | Git Secret Exclusion | Master Plan 1.3, 1.8; DEC-003 | `P00-T04` / `P01-T04` | `.env`, `.env.*` (except `.env.example`), `data/`, `logs/`, `tmp/` ignored; 0 secrets in Git | `VERIFIED (P00-T04)` |
| **ACC-002A** | Secret Masking & Redaction | Master Plan 1.8; ADR-001 | `P01-T04` / `P02-T05` | UI masks keys (`••••1234`); raw keys never appear in logs, console, or tracebacks | `PLANNED` |
| **ACC-003** | Missing Key Graceful Handling | Master Plan 1.8; ADR-001 | `P01-T04` / `P02-T05` | App boots normally with missing key; provider shows "Not Configured"; zero crash | `BLOCKED (Deferred to P01)` |
| **ACC-004** | Project Creation & Persistence | Master Plan 1.4; Product Rules 2 | `P03-T01` | SQLite persists project row with canonical UUID v4, ratio, language, timestamp | `PLANNED` |
| **ACC-005** | 4-Project Cap / Confirmation | Master Plan 1.4; DEC-019 | `P04-T04` | 5th project triggers prompt naming oldest project; NO/Cancel aborts creation | `PLANNED` |
| **ACC-006** | 5th Project Atomic Replacement | Master Plan 1.4; DEC-019 | `P04-T04` | Explicit YES executes replacement; active project count remains strictly 4 | `PLANNED` |
| **ACC-006A** | Replacement Crash Rollback | Master Plan 1.4; DEC-019 | `P04-T04` | Simulated failure during replacement restores original oldest project; 0 data loss | `PLANNED` |
| **ACC-007** | Cross-Project Tenant Isolation | Master Plan 1.3; Product Rules 2 | `P03-T02` | Requests scoped to Project A cannot read, query, or mutate Project B data | `PLANNED` |
| **ACC-008** | Aspect Ratio Configuration | Master Plan 1.5; Product Rules 3 | `P03-T01` | 9:16 vertical enforces 1080x1920; 16:9 landscape enforces 1920x1080 | `PLANNED` |
| **ACC-009** | Vertical Duration Exact Bounds | Master Plan 1.5; Baseline 3 | `P05-T01` | T in {24, 32, 40, 48, 56}s; exactly N = T / 8 parts; every part d_i == 8.0s; SUM == T | `PLANNED` |
| **ACC-009A** | Vertical Part Duration Tampering | Master Plan 1.5; Baseline 3 | `P05-T01` | Rejection of any non-8.0s part duration, mismatched part count, or sum error | `PLANNED` |
| **ACC-010** | Unsupported Vertical Duration | Master Plan 1.5; Baseline 3 | `P05-T01` | Submitting unsupported duration (e.g. 60s) raises explicit error; no silent coercion | `PLANNED` |
| **ACC-011** | Landscape Duration Minimum | Master Plan 1.5; Baseline 3 | `P05-T01` | Submitting landscape duration T < 180.0s rejected with explicit validation error | `PLANNED` |
| **ACC-012** | Landscape Part Duration Bounds | Master Plan 1.5; Baseline 3 | `P05-T01` | System enforces 0.0 < d_i <= 8.0s for every landscape part; rejects out-of-bounds | `PLANNED` |
| **ACC-012A** | Landscape Part Duration Sum | Master Plan 1.5; Baseline 3 | `P05-T01` | System enforces SUM(d_i) == T; rejects candidates where parts sum differs from T | `PLANNED` |
| **ACC-013** | Source Fetch Failure Handling | Master Plan 1.6; Baseline 4 | `P04-T02` | Failed URL fetch marks source Not Validated; displays error; manual paste active | `PLANNED` |
| **ACC-014** | Unvalidated Source Gate | Master Plan 1.6; Baseline 4 | `P04-T03` | Script generation disabled in UI and blocked on API for unsaved/unvalidated source | `PLANNED` |
| **ACC-015** | Source Edit Stale Marking | Master Plan 1.6; Baseline 4 | `P04-T03` | Modifying source increments version and marks downstream script/outputs "Stale" | `PLANNED` |
| **ACC-016** | Skill A Contract Conformity | Master Plan 1.2; Skill A Spec | `P09-T03` | Generated script conforms to JSON schema: title, parts with duration, narration, visuals | `PLANNED` |
| **ACC-016A** | Skill A Hindi Devanagari | Master Plan 1.2, 1.5; Skill A | `P09-T03` | Hindi narration & VO directions strictly in Devanagari script (U+0900 to U+097F) | `PLANNED` |
| **ACC-016B** | Skill A Hook-Story-Ending | Master Plan 1.2; Skill A Spec | `P09-T04` | Strict structural sequence: Part 1 Hook, Parts 2..N-1 Story, Part N Ending/CTA | `PLANNED` |
| **ACC-017** | Saved Script Preservation | Master Plan 1.7; Baseline 4 | `P09-T04` | Script regeneration failure preserves existing saved script untouched in DB | `PLANNED` |
| **ACC-018** | Latest-Only Script Overwrite | Master Plan 1.7; Baseline 4 | `P08-T03` | Saving new script candidate replaces prior version; zero prior script history kept | `PLANNED` |
| **ACC-019** | Approval Invalidation on Edit | Master Plan 1.7; Baseline 4 | `P08-T02` | Editing script sets `approved = false` and blocks downstream Skills B, C, D | `PLANNED` |
| **ACC-020** | Exact Script Hash Approval Gate | Master Plan 1.7; Baseline 4 | `P08-T04` | Script hash locked on approval; unlocks Skills B, C, D strictly for approved hash | `PLANNED` |
| **ACC-021** | Skill B Video Prompts per Part | Master Plan 1.2; Skill B Spec | `P10-T02` | Exactly one visual prompt per script part; zero claims of generating video files | `PLANNED` |
| **ACC-021A** | Skill B Field Separation | Master Plan 1.2; Skill B Spec | `P10-T02` | `scene_visual_prompt` and `audio_direction` separated; zero dialogue in visual prompt | `PLANNED` |
| **ACC-022** | Video Prompt Staleness | Master Plan 1.7; Baseline 4 | `P10-T03` | Script modifications mark existing video prompts "Stale"; regeneration required | `PLANNED` |
| **ACC-023** | Skill C Single Thumbnail Prompt | Master Plan 1.2; Skill C Spec | `P11-T02` | Exactly one cohesive thumbnail prompt generated for the entire video project | `PLANNED` |
| **ACC-023A** | Skill C Devanagari & Ratio | Master Plan 1.2, 1.5; Skill C | `P11-T02` | Hindi thumbnail text overlay in Devanagari; aspect ratio matches project setting | `PLANNED` |
| **ACC-024** | Skill D English Content Mode | Master Plan 1.2; Skill D Spec | `P12-T02` | Content language English generates YouTube SEO package in Roman Hindi | `PLANNED` |
| **ACC-024A** | Skill D 100% Roman Hindi | Master Plan 1.2; Skill D Spec | `P12-T02` | All 5 SEO fields in Roman Hindi (Latin alphabet); strictly 0 Devanagari characters | `PLANNED` |
| **ACC-024B** | Skill D Tags Format | Master Plan 1.2; Skill D Spec | `P12-T02` | Tags formatted strictly as comma-separated string; zero hashtags or bullet numbers | `PLANNED` |
| **ACC-024C** | Skill D Zero Fake Metrics | Master Plan 1.2; Skill D Spec | `P12-T02` | Output contains zero fabricated search volumes, estimated clicks, CPC, or ranks | `PLANNED` |
| **ACC-025** | No-Silent-Switch Model Fallback | Master Plan 1.8; DEC-010 | `P05-T04` | Primary model failure halts and prompts for explicit user permission before alternate | `PLANNED` |
| **ACC-026** | Zero Blind Retry on Auth/4xx | Master Plan 1.8; Product Rules 5 | `P05-T05` | 401, 403, 404 return immediate failure; exactly 0 retries executed | `PLANNED` |
| **ACC-026A** | Bounded Transient Retry | Master Plan 1.8; Product Rules 5 | `P05-T05` | Bounded retry (max attempts with backoff) for safe transient errors (503/timeout) | `PLANNED` |
| **ACC-027** | Pydantic Schema Validation | Master Plan 1.8; ADR-001 | `P05-T05` | Malformed or partial LLM JSON fails Pydantic schema validation; rejected from DB | `PLANNED` |
| **ACC-028** | Debouncing Duplicate Jobs | Master Plan 1.9; Baseline 6 | `P06-T02` | Rapid duplicate generation clicks rejected/debounced; 0 duplicate concurrent jobs | `PLANNED` |
| **ACC-029** | Background Job Failure Recovery | Master Plan 1.9; Baseline 6 | `P06-T03` | Provider disconnect marks job `FAILED`; truthful error recorded; retry restored | `PLANNED` |
| **ACC-030** | Truthful Usage / Cost Display | Master Plan 1.8; Baseline 5 | `P06-T04` | Missing token cost displayed as "Estimate" or "Unknown"; zero invented costs | `PLANNED` |
| **ACC-030A** | 100-Record Retention Cap (FIFO) | Master Plan 1.9; DEC-018 | `P06-T04` | 101st execution job prunes oldest history record; history remains exactly 100 | `PLANNED` |
| **ACC-030B** | History Metadata Only | Master Plan 1.9; DEC-018 | `P06-T04` | History table stores metadata only; strictly 0 raw prompts, source text, or payloads | `PLANNED` |
| **ACC-031** | Data-Only Export Archive | Master Plan 1.10; ADR-001 | `P13-T01` | Export ZIP includes scripts, prompts, SEO; 100% excludes `.env`, secrets, DB, logs | `PLANNED` |
| **ACC-032** | Cascade Delete & .env Safety | Master Plan 1.4; DEC-018 | `P13-T02` | Project delete cleans DB row, temp files, history; preserves shared `.env` untouched | `PLANNED` |
| **ACC-033** | Module E Partial Connector Status | Master Plan 1.11; Product Rules 7 | `P14-T02` | Research UI truthfully indicates connector status; unconfigured not claimed scanned | `PLANNED` |
| **ACC-034** | Module E 4-Idea Ranking | Master Plan 1.11; Product Rules 7 | `P14-T03` | Ranking yields up to 4 ideas; separates trend confidence from evidence confidence | `PLANNED` |
| **ACC-035** | Module E Topic Dossier Citations | Master Plan 1.11; Product Rules 7 | `P14-T04` | Dossier includes verifiable citations, timestamps, and conflicting evidence | `PLANNED` |
| **ACC-036** | Module E User-Confirmed Import | Master Plan 1.11; Product Rules 7 | `P14-T05` | Importing dossier populates Source Panel; requires explicit user Save & Validation | `PLANNED` |
| **ACC-037** | Full Test Suite Clean Regression | Master Plan 1.12; TASK_CONTRACT | `P15-T01` | Entire automated pytest suite passes cleanly with zero regression across modules | `PLANNED` |
| **ACC-038** | Clean-Install Verification | Master Plan 1.13; ADR-001 | `P15-T05` | Fresh machine install following README succeeds without undocumented steps | `PLANNED` |

---

## 2. Invariant & Decision Traceability

- **`DEC-001` (Source of Truth):** `99_REFERENCE_SOURCE/01_MASTER_PLAN_APPROVED_ORIGINAL.md` preserved verbatim. Zero silent changes.
- **`DEC-002` (Hinglish Reference):** Hinglish text used exclusively for developer guidance and rationale; not user-facing text.
- **`DEC-003` (Plaintext `.env` Trade-off & Secret Safety):** Secrets stored in local root `.env`, permanently Git-ignored, masked in UI, 0 keys in logs or export archives. Verified via ACC-002 (PASSED).
- **`DEC-004` (Skills A–D Contracts):** Skill specifications in `99_REFERENCE_SOURCE/` (files 04–07) are immutable prompt contracts.
- **`DEC-005` (Acceptance Matrix Blueprint):** `05_TESTING/ACCEPTANCE_MATRIX_PROPOSED.md` is the official 53-test testing blueprint.
- **`DEC-006` (ADR-001 Stack):** Python 3.12, FastAPI, Pydantic v2, SQLite, SQLAlchemy+Alembic, localhost web UI, pytest.
- **`DEC-007` (AI Provider Candidacy):** Remains strictly `OPEN`. Google Gemini candidate 1, Groq alternate candidate; neither supported until live tests pass.
- **`DEC-010` (No Silent Model Switch):** Strict halt and permission prompt on primary model failure (ACC-025).
- **`DEC-015` (Localhost Binding):** Binds to 127.0.0.1 (ACC-001A marked `PROPOSED / OUT-OF-BASELINE`).
- **`DEC-018` (Execution History Retention & Metadata Policy):** Max 100 records/project FIFO (ACC-030A), metadata only (ACC-030B), cascade delete on project removal, shared `.env` immutability (ACC-032).
- **`DEC-019` (Active Project Limit Capped at 4):** Hard cap of 4 active saved projects. 5th project triggers exact confirmation prompt naming oldest project; NO/Cancel aborts; explicit YES performs two-phase crash-resilient replacement (ACC-005, ACC-006, ACC-006A).

---

## 3. Phase Milestone Exit Gates (P00 through P15)

| Phase | Milestone Name | Mandatory Exit Gates & Requirements |
|---|---|---|
| **P00** | **Requirements & Baseline Freeze** | All authoritative source contracts imported; ADR-001 approved; DEC-003, DEC-018, DEC-019 ratified; pre-coding security setup verified (`.gitignore`, `.env.example`, Git initialized; ACC-002 PASSED); traceability matrix frozen; zero code written. |
| **P01** | **Repository Skeleton & Runtime** | Repeatable virtual environment; locked dependencies installed; server entrypoint; test runner and linting active; ACC-001, ACC-002A, ACC-003 pass. |
| **P02** | **Configuration & Secret Safety** | Typed config loader; Notepad `.env` edit workflow; secret redaction in tracebacks and logs; ACC-002A, ACC-003, ACC-030 pass. |
| **P03** | **Domain Models & SQLite** | SQLite schema & Alembic migrations; UUID v4 entity keys; cross-project tenant isolation; temp directory isolation; ACC-004, ACC-007 pass. |
| **P04** | **Project Manager & 4-Project Cap** | Create/list/open project; ratio settings (9:16 vs 16:9); 4-project limit transactional enforcement with confirmation dialogue; ACC-005, ACC-006, ACC-006A, ACC-008 pass. |
| **P05** | **Provider Interface & Adapter** | Typed provider adapter; live connection verification; duration calculators ({24..56}s vertical, >=180s landscape); model failover consent; schema validation; ACC-009 through ACC-012A, ACC-025, ACC-026, ACC-026A, ACC-027 pass. |
| **P06** | **Jobs, Usage & Execution History** | Job queue state machine; debouncing duplicate jobs; bounded retries; 100-record FIFO execution history pruning; metadata-only storage; ACC-028, ACC-029, ACC-030, ACC-030A, ACC-030B pass. |
| **P07** | **Source Adding Panel** | URL and text source ingestion; readability validation; HTTP 404/failure handling; unvalidated source gate; ACC-013, ACC-014, ACC-015 pass. |
| **P08** | **Analysis Reuse & Approval Gates** | Analysis caching; source invalidation engine; latest-only script candidate replacement; backend script hash approval lock; ACC-015, ACC-018, ACC-019, ACC-020 pass. |
| **P09** | **Skill A — Story-to-Script** | Prompt contract binding; JSON script schema; Devanagari Hindi validation; Hook-Story-Ending structure; failed candidate preservation; ACC-016, ACC-016A, ACC-016B, ACC-017 pass. |
| **P10** | **Skill B — Video Prompts** | Part-by-part prompt generation; prompt field separation; zero dialogue in visuals; script change staleness marking; ACC-021, ACC-021A, ACC-022 pass. |
| **P11** | **Skill C — Thumbnail Intelligence** | Single cohesive thumbnail prompt; Devanagari text overlay; aspect ratio matching; ACC-023, ACC-023A pass. |
| **P12** | **Skill D — YouTube SEO Engine** | 100% Roman Hindi in Latin alphabet across all 5 fields; zero Devanagari chars; comma-separated tags; zero fake metrics; ACC-024, ACC-024A, ACC-024B, ACC-024C pass. |
| **P13** | **Export, Deletion & Core Acceptance** | Data-only ZIP export (0 secrets, 0 database, 0 logs); atomic cascade project deletion; shared `.env` preserved untouched; ACC-031, ACC-032 pass. |
| **P14** | **Optional Module E — Idea Research** | Research connector status; 4-idea ranking; topic dossier with citations; user-confirmed import to Source Panel; ACC-033, ACC-034, ACC-035, ACC-036 pass. |
| **P15** | **Regression, Packaging & Release** | Full automated test suite passes; fresh machine clean install from README; update/migration rollback verified; ACC-037, ACC-038 pass. |

---

## 4. Evidence Standards & Recording Responsibilities

1. **Who Records Evidence:**
   - The primary implementing software engineer records verifiable execution evidence upon completing each task.
2. **What Constitutes Valid Evidence:**
   - Terminal stdout/stderr execution logs from automated test runs (e.g. `pytest` command, exit code 0, test pass counts).
   - Database inspection snapshots and query outputs for state assertions.
   - Filesystem verification logs (`git status --ignored`, `git check-ignore`, archive manifests).
3. **Strict Prohibition on Inferring Pass:**
   - No test may be marked `PASSED` or `VERIFIED` based on code inspection or implementation appearance alone.
   - Any test that has not been executed with recorded output must remain `PLANNED` or `NOT RUN`.
   - Any test blocked by a missing prerequisite must be marked `BLOCKED`.

---

## 5. Release Readiness Criteria

1. **Core Local-First Application Release:**
   - All 52 approved baseline acceptance tests (`ACC-001` through `ACC-038`) pass with recorded evidence.
   - P00 through P13 exit gates verified.
   - Zero secrets committed, exposed in UI, logged, or included in exports.
   - Shared `.env` immutability verified across project deletion and history retention.
   - 4-project active limit and 100-record execution history retention verified.
2. **Module E Discovery Extension (Optional):**
   - Core application stable; ACC-033 through ACC-036 pass with verified API connector terms.
3. **Standalone Distribution Package (Optional):**
   - Clean install smoke test passes following README instructions alone (ACC-038).

---

## 6. Formal P00 Phase Sign-Off

- **Prerequisites P00-T01 through P00-T04:** Verified and documented.
- **Documentation Inconsistencies:** Resolved (4-project cap aligned in readiness checklist; task IDs synchronized in acceptance matrix).
- **Security Blocker:** Resolved (root `.gitignore` excludes `.env`, `.env.*` except `.env.example`, `data/`, `logs/`, `tmp/`; sanitized `.env.example` created; Git initialized; ACC-002 PASSED).
- **Runtime Application Code:** Strictly deferred to P01 (ACC-003 remains `BLOCKED / NOT RUN`).
- **Phase Order:** Strictly frozen. Next permitted phase is **`P01`** (`Repository Skeleton & Repeatable Python Runtime`).
