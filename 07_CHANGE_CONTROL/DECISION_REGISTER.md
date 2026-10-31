# Decision Register — Must Be Maintained During Build

Status values: `OPEN`, `PROPOSED`, `APPROVED`, `REJECTED`, `IMPLEMENTED`, `VERIFIED`.

| ID | Decision | Current status | Required resolution / rule |
|---|---|---|---|
| DEC-001 | Source of truth | APPROVED | Original `01_MASTER_PLAN_APPROVED_ORIGINAL.md`; no silent changes |
| DEC-002 | Local-first Python deployment | APPROVED BASELINE AMENDMENT | User-approved: Local-first Python app installed via GitHub; specific Python version, OS support and install flow deferred to P00-T03 |
| DEC-003 | Local plaintext `.env` editable in Notepad | APPROVED BASELINE AMENDMENT | User-approved: Local plaintext `.env` editable in Notepad; strict security invariants: .env git-excluded, placeholder-only .env.example, never logged, never exported in ZIP, secrets masked in UI |
| DEC-004 | Four original skill prompt files | APPROVED | User explicit sign-off (2026-10-30) approving Skill A, Skill B, Skill C, and Skill D revised specifications (`99_REFERENCE_SOURCE/04_SKILL_A_STORY_TO_SCRIPT_SPEC.md`, `99_REFERENCE_SOURCE/05_SKILL_B_VIDEO_PROMPT_ENGINEERING_SPEC.md`, `99_REFERENCE_SOURCE/06_SKILL_C_THUMBNAIL_INTELLIGENCE_SPEC.md`, `99_REFERENCE_SOURCE/07_SKILL_D_YOUTUBE_SEO_ENGINE_SPEC.md`) strictly as authoritative architectural/functional documentation contracts. Implementation deferred to build phases. |
| DEC-005 | Original `09_TEST_AND_ACCEPTANCE_MATRIX.md` | APPROVED | User explicit sign-off (2026-10-30) approving the revised proposed Acceptance Matrix at `/05_TESTING/ACCEPTANCE_MATRIX_PROPOSED.md` strictly as the official Testing Blueprint and Acceptance Matrix (51 unique test IDs: 50 approved baseline tests + 1 proposed out-of-baseline test ACC-001A tied to DEC-015). Implementation deferred to build phases. |
| DEC-006 | Technology stack: Python, FastAPI, Pydantic, SQLite | APPROVED | User explicit sign-off (2026-10-29) on ADR-001 (`02_ARCHITECTURE/ADR_001_TECHNOLOGY_STACK.md`) at architectural documentation level: Python 3.12, FastAPI, Pydantic v2 (schema/type validation only), SQLite, SQLAlchemy+Alembic, localhost web UI, pytest. Verification of Windows wheels and migration rollback procedures pending in Phase P01. |
| DEC-007 | First real provider adapter | OPEN | Select only after checking user access, model capability and structured-output needs; Groq is a candidate, not assumed supported |
| DEC-008 | Provider and model names/capabilities | OPEN | Verify official/current APIs during implementation; unknown remains Unknown |
| DEC-009 | Local secret store for future nontechnical users | PROPOSED | `.env` first for requested mode; consider OS keyring only if approved |
| DEC-010 | Idea Research Module E | APPROVED BASELINE AMENDMENT | User-approved: Optional pre-source discovery module strictly separate from Skills A-D; trend vs evidence confidence separate; transparent citations; explicit user review and import action required before source panel |
| DEC-011 | Research connectors for MVP | OPEN | Decide which adapters are mandatory vs optional; do not claim unsupported coverage |
| DEC-012 | PyTrends | PROPOSED EXPERIMENTAL | Unofficial/archived dependency; not a core dependency; replaceable adapter |
| DEC-013 | Keyword Tool access | OPEN | Separate manual/free web use from any paid API; verify terms/pricing at implementation time |
| DEC-014 | Idea ranking score weights | OPEN | Define versioned/explainable formula before Module E release; trend and factual confidence separate |
| DEC-015 | Local UI exposure | PROPOSED | Bind localhost by default; any LAN/network access requires explicit security decision |
| DEC-016 | Executable packaging | OPTIONAL LATER | Only after regression and clean-install acceptance pass |
| DEC-017 | Research dossier in ZIP export | PROPOSED | Decide schema; never export secrets; no restore feature unless separately approved |
| DEC-018 | Execution history retention | APPROVED BASELINE AMENDMENT | User-approved (2026-10-30): Retain only the latest 100 execution history records per project (FIFO pruning). Store metadata only (timestamps, latency, token usage, model, provider, status, sanitized error code); strictly do not persist raw prompts, raw source text, or raw LLM request/response payloads. Delete project-specific history when that project is deleted. Never delete or modify the shared .env file under any circumstance. |
| DEC-019 | Baseline amendment: Active project limit reduction to 4 | APPROVED BASELINE AMENDMENT | User-approved (2026-10-30): Maximum active saved projects reduced from 6 to 4. Creating 5th project prompts user: "You already have 4 projects. Do you want to delete the oldest project and create this new project?" naming the oldest project. If user selects NO or cancels, all 4 existing projects are retained and new project creation is aborted. Only explicit YES deletes the oldest project and creates the new one in an atomic/recoverable transaction. Automatic deletion is strictly prohibited. |

## Change procedure

1. Describe the requested change and the rule it modifies.
2. Identify impacted files, phases, data migrations, tests and security risks.
3. Obtain explicit user approval for changes to the baseline/skill contract.
4. Update this register and changelog before implementation.
5. Update requirements and acceptance tests.
6. Implement only after dependencies and acceptance criteria are updated.
