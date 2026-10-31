# Architecture Decision Record (ADR-001)
# Technology Stack for ILLUM AI STUDIO Local Runtime

**Status:** APPROVED (Architectural Documentation Sign-off)  
**Date:** 2026-10-29  
**Decision Owner:** Lead Developer & System Architect  
**Related Decisions:** DEC-002 (Local-first Python), DEC-003 (Local .env), DEC-006 (Technology Stack), DEC-010 (Module E)  
**Governing Phase:** P00 — Requirements and Baseline Freeze (Task P00-T03)

---

## 1. Context and Problem Statement

ILLUM AI STUDIO requires a local-first, reliable, and user-friendly technology stack for video production scripting, prompt engineering, thumbnail intelligence, and YouTube SEO metadata generation. 

The primary user is a non-technical beginner operating in a Windows environment who:
- Downloads/clones the repository from GitHub.
- Configures AI provider API keys locally in a plain-text `.env` file using Notepad.
- Launches the application via a simple batch script (`run.bat`).
- Interacts with the studio through a local web browser interface (`http://127.0.0.1:8000`).

The stack must strictly uphold all core invariants defined in the Master Architecture and Baseline Rules:
1. **Complete data isolation across projects:** Enforced via application-level authorization and project scoping; maximum 4 active saved projects (DEC-019).
2. **Strict schema and duration invariants:**
   - **9:16 vertical shorts:** Aspect ratio 9:16, target resolution 1080x1920. Approved total durations are strictly 24, 32, 40, 48, or 56 seconds (with corresponding 3, 4, 5, 6, or 7 parts). Every part duration is exactly 8 seconds (`part_duration_seconds == 8.0`). Structure: Hook + story parts + Ending. (60 seconds is explicitly not approved).
   - **16:9 landscape videos:** Aspect ratio 16:9, target resolution 1920x1080. Minimum total duration is 180 seconds. Every part duration must be greater than 0 seconds and at most 8 seconds. Mathematical rule: `0 < part_duration_seconds <= 8`. The sum of all part durations must equal the total script duration (`sum(part_durations) == total_duration`).
3. **Hard approval gates:** Downstream skills remain disabled until the exact script version hash is approved by the user.
4. **Secret protection:** API keys never committed to Git, never logged in terminal/tracebacks, never included in project export ZIPs, and masked in the UI.
5. **No silent AI model switching:** If a preferred model fails, the system must not silently failover to an alternative model without explicit user permission.

---

## 2. Proposed Technology Stack

| Layer / Component | Proposed Technology | Selection Rationale | Status |
|---|---|---|---|
| **Programming Language & Runtime** | **Python 3.12** (Primary Candidate) | Broadest long-term support, high performance, pre-compiled wheels on Windows for all standard libraries, robust type hinting. | `PENDING VERIFICATION` (Windows fresh install check) |
| **Web Server & Backend API** | **FastAPI** + **Uvicorn** (ASGI) | Native asynchronous support, automatic OpenAPI docs, zero external server daemon, and direct binding to localhost (`127.0.0.1`). | Proposed |
| **Schema & Structural Validation** | **Pydantic v2** | Enforces structural, type, and payload schema validation on API inputs/outputs. Separated from business-rule and factual truth validation. | Proposed |
| **Local Database Engine** | **SQLite** (File-based, `data/illum.db`) | Zero configuration, built into Python, serverless, single-file isolation, easily backed up, and perfectly suited for single-user local applications. | Proposed |
| **ORM & Database Abstraction** | **SQLAlchemy 2.0** | Robust, type-safe database mapping, explicit query scoping by `project_id`. | Proposed |
| **Database Migrations** | **Alembic** | Versioned schema migration management. Requires pre-migration backups and rollback testing before release. | `PENDING VERIFICATION` (Rollback procedures) |
| **Presentation / UI Layer** | **Localhost Embedded Web UI** (HTML / Tailwind / Vanilla JS or HTMX) | Served directly by FastAPI; requires **ZERO Node.js or npm** dependencies on the user's computer, dramatically simplifying Windows execution. | Proposed |
| **Configuration & Secrets** | **python-dotenv** | Reads local `.env` file at application startup. Strict `.gitignore` enforcement. | Proposed |
| **Automated Testing Suite** | **pytest** + **pytest-asyncio** + **httpx** | Fast, deterministic testing of all domain models, state machines, API endpoints, secret sanitization, and approval gate invariants. | Proposed |

---

## 3. Component Details & Architectural Invariants

### 3.1 Operating System & Runtime Environment
- **Primary Target:** Windows 10 and Windows 11 (64-bit).
- **Secondary Targets:** macOS (Apple Silicon / Intel) and modern Linux distributions (Ubuntu/Debian).
- **Python Version Strategy:** Python 3.12 is the primary recommendation. If specific binary dependencies exhibit friction on Windows during Phase P01, Python 3.11 is the immediate fallback. Both versions share identical typing and Pydantic v2 capabilities.
- **Verification Criteria:** Clean install in a fresh virtual environment (`venv`) on Windows without native compilation tools (`C++ Build Tools` not required).

### 3.2 UI Framework Implementation Approach
To maintain the simplest installation workflow for a non-technical beginner:
- **Recommended Approach:** Fast, embedded responsive HTML templates utilizing Tailwind CSS (standalone/CDN) and lightweight vanilla JavaScript or HTMX.
- **Why avoid a separate React/Vite frontend build?** Requiring Node.js and npm forces the beginner to maintain two separate runtime environments (Node + Python). An embedded web UI served by FastAPI requires **only Python** on the machine.
- **Localhost Security Caveat:** The web server binds strictly to `127.0.0.1:8000` (localhost) to prevent external LAN exposure. However, binding to localhost is **not a complete security guarantee** (e.g., malicious local processes on the same machine could still attempt requests). Host-level process isolation and restricted file permissions are advised.

### 3.3 Database, Migrations, and Project Isolation
- **Storage Location:** `data/illum.db` (strictly excluded in `.gitignore`).
- **Maximum 4 Active Projects Constraint (DEC-019):**
  - Enforced at the application service layer.
  - When the user attempts to create a 5th project, the system must prompt: `"You already have 4 projects. Do you want to delete the oldest project and create this new project?"`, identifying the oldest project by `created_at` timestamp and display name.
  - **Without explicit user confirmation, NO deletion occurs.**
  - If the user cancels or selects NO, **both the deletion of the oldest project and the creation of the new project are aborted**, strictly retaining all 4 existing projects.
  - Atomic deletion is a technical recovery safeguard to prevent orphaned data; it is **NOT an automatic permission** to delete projects without explicit consent.
- **Database Migration Safety (Alembic):**
  - Using a migration tool does **not automatically guarantee data safety**.
  - Essential verification items prior to release:
    1. Automated pre-migration database file backup (`data/illum.db.bak`).
    2. Isolated migration upgrade and downgrade tests in CI/test suites.
    3. Documented manual recovery and rollback procedure in the operations guide.
- **Project Isolation:**
  - A database column (`project_id`) or index alone is **not sufficient security**.
  - Every project-scoped read, write, update, and delete operation requires explicit application-layer scope and authorization checks enforcing `project_id`.
  - Queries must bind `project_id` directly; cross-project data retrieval without explicit recorded user approval is strictly prohibited.

### 3.4 Validation Boundaries and Pydantic Schema Role
- **Pydantic Schema Validation Scope:**
  - Validates primitive data types, field presence, and field-level numerical/structural constraints on API payloads and model outputs.
  - **Numeric & Finite Duration Requirements:** Every part duration must be a finite, positive number.
  - **Part Duration Bounds:**
    - **16:9 Landscape part bounds:** Each part duration must satisfy the strict condition `0 < part_duration_seconds <= 8`.
    - **9:16 Vertical part bounds:** Each part duration must be exactly 8 seconds (`part_duration_seconds == 8.0`).
- **Separation from Cross-Field Business-Rule Validation:**
  - Relational and multi-field business rules are enforced at the domain/service logic layer, not conflated with Pydantic single-field type checks:
    - Verifying that the sum of all part durations equals the total script duration (`sum(part_durations) == total_duration`).
    - Verifying that total duration and part counts match the approved plan (e.g., 24s/3 parts, 32s/4 parts, 40s/5 parts, 48s/6 parts, 56s/7 parts for 9:16; $\ge 180$s for 16:9).
    - Verifying active project count $\le 4$ (DEC-019).
    - Verifying approval hash match before unlocking downstream skills.
- **Separation from Factual & Linguistic Content Validation:**
  - Pydantic schema validation **DOES NOT guarantee factual correctness, truthfulness, source-grounding, or Devanagari linguistic accuracy**.
  - Whether a script invents unsupported facts, preserves evidence traceability, or writes valid Hindi in Devanagari script is strictly governed by skill-specific analysis and validation pipelines (e.g., Skill A Story-to-Script validation checks), not by JSON schema validation.

### 3.5 Secret Management and Security Invariants (DEC-003)
- **Local `.env` Workflow:** User copies `.env.example` to `.env` and edits keys in Notepad.
- **Plaintext Trade-off:** The file is plain text and unencrypted. The application documents this trade-off explicitly and warns against shared computer risks.
- **Git Safety:** `.env` is permanently excluded via `.gitignore`.
- **Placeholder Safety:** `.env.example` contains only placeholder keys (`GEMINI_API_KEY=`, `GROQ_API_KEY=`), never real credentials.
- **Mandatory Security Verification Tests:**
  - Automated tests scanning application logs and terminal output to verify detected secrets are redacted.
  - Exception and traceback handlers tested to ensure configuration objects never leak secrets.
  - Project export ZIP tests verifying `.env`, `logs/`, and `data/illum.db` are completely excluded.
  - UI tested to ensure provider keys are masked (e.g., `sk-...12a4`) and never displayed in full plain text.

### 3.6 Approval Gates and Model Rules
- **Script Approval Gate:** Downstream skills (Skill B Video Prompts, Skill C Thumbnail Prompt, Skill D SEO Package) remain disabled until the exact hash of the current script version is approved by the user. Editing or regenerating the script invalidates downstream outputs and resets approval state.
- **AI Model Routing & Fallback:** The Provider Manager routes requests through configured adapters. If a preferred model fails, the system presents the error and asks the user for explicit permission to use an alternative model. **No silent automatic failover is permitted.**

### 3.7 Testing Strategy
- **Unit Tests:** Verify duration mathematics (exact 8-second parts for 9:16; `0 < part_duration_seconds <= 8` and total duration $\ge 180$s for 16:9; `sum(part_durations) == total_duration`), language rules (Devanagari script validation), script hashing, and state transitions.
- **Integration Tests:** Verify FastAPI route handlers, database transactions, project deletion limits, and error sanitization using `httpx.AsyncClient`.
- **Security Tests:** Sentinel secret strings are injected into test runs to verify they never appear in log files, error outputs, or generated export archives.

---

## 4. Rejected Alternatives

1. **Streamlit:**
   - *Reason for Rejection:* Streamlit re-executes the entire Python script from top to bottom on every user click or widget interaction. This reactive execution model makes it fragile and error-prone to maintain complex multi-step state machines, precise script version hashing, and strict approval gates. It also introduces large, unnecessary machine-learning dependencies and makes clean automated testing cumbersome.
2. **Decoupled Node.js / React Frontend:**
   - *Reason for Rejection:* Requires the non-technical user to install and maintain both Node.js (with npm) and Python on Windows, creating significant friction, build failures, and port management issues.
3. **Local PostgreSQL or MySQL Server:**
   - *Reason for Rejection:* Requires background database server services, credentials, and port configuration. Unnecessary operational complexity for a local single-user desktop application. SQLite satisfies all relational and migration needs without external services.

---

## 5. Unresolved Decisions, Risks, and Next Steps

1. **First AI Provider Adapter (DEC-007):** Status is `OPEN`. Candidate adapters (e.g. Groq, Google Gemini) will be evaluated in Phase P00-T04 / Phase P05 based on structured JSON output reliability and user access.
2. **Module E Connector Decisions (as recorded in DECISION_REGISTER.md):**
   - **DEC-011 (Research connectors for MVP):** Status is `OPEN`. Connectors will be evaluated when Module E is designed in Phase P14.
   - **DEC-012 (PyTrends):** Status is `PROPOSED EXPERIMENTAL`. Unofficial/archived dependency; not a core dependency; replaceable adapter.
   - **DEC-013 (Keyword Tool access):** Status is `OPEN`. Separate manual/free web use from any paid API; verify terms/pricing.
   *(Note: The statuses of DEC-011, DEC-012, and DEC-013 remain unchanged and are not altered by this ADR).*
3. **Fresh Windows Wheel Verification:** In Phase P01, verify that all pinned dependencies install cleanly on Windows without requiring Microsoft C++ Build Tools.

---

## 6. Decision Status & Sign-off

- **Current Status:** `APPROVED` (User signed off on 2026-10-29 strictly at the architectural documentation level).
- **Scope of Approval:** This approval ratifies the architectural technology-stack selection (Python 3.12, FastAPI, Pydantic v2, SQLite, SQLAlchemy, Alembic, localhost web UI, pytest). It does not claim or imply implementation readiness or that runtime testing has occurred.
- **Pending Verification Items:**
  1. Python 3.12 Windows 64-bit clean virtual environment wheel installation without C++ Build Tools (to be verified in Phase P01).
  2. Alembic migration safety: automated pre-migration backup, upgrade/downgrade migration testing, and manual rollback/recovery procedures before release.
