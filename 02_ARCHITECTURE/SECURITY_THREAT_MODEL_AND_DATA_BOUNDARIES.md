# Security Threat Model and Data Boundaries Specification

**Status:** PROPOSED TECHNICAL DESIGN (DOCUMENTED)  
**Task Association:** `P00-T04 — Freeze connector, credentials and retention boundaries`  
**Governing Architecture:** Python 3.12 / FastAPI / SQLite Local-First Desktop Application  
**Related Decisions:** `DEC-003` (Approved), `DEC-007` (Open), `DEC-018` (Approved), `DEC-019` (Approved)  

---

## 1. Executive Summary & Governance Scope

This document establishes the formal threat model, security boundaries, and crash-recovery protocols for ILLUM AI Studio. It defines the operational constraints governing local credential storage, filesystem mutations, project lifecycle replacement, database atomicity, and multi-tenant project isolation within a single-user local environment.

### Governance Invariants Preserved:
1. **`DEC-003` (Local `.env` Credential Security):** Credentials reside in a local plaintext `.env` file at the repository root, permanently ignored by Git, never exported in archives, masked in UI, and never described as encrypted.
2. **`DEC-007` (AI Provider Candidacy):** Remains strictly `OPEN`. Google Gemini is selected as First Candidate and Groq as Alternate Candidate. Neither provider is approved, implemented, or supported until live connectivity and structured-output schema validation tests pass.
3. **`DEC-018` (Execution History Retention & Metadata Policy):** Strictly capped at the latest 100 execution history records per project via FIFO pruning. Persists operational metadata only; strictly zero raw prompts, raw source text, or raw LLM request/response payloads in database logs. Deleting a project cascades to delete its history. The shared `.env` file must never be deleted or modified.
4. **`DEC-019` (Project Retention & Reversible Replacement):** Hard cap of 4 active saved projects. Attempting to create a 5th project prompts the user with the exact approved dialogue naming the oldest project. Creation aborts if NO or Cancel is selected. Replacement occurs only after explicit YES via a two-phase crash-resilient protocol that guarantees zero partial loss of existing projects.

---

## 2. 12-Domain Threat Model Matrix

| # | Threat Domain | Asset at Risk | Threat Scenario | Potential Impact | Required Mitigation | Governing Reference | Verification Target |
|---|---|---|---|---|---|---|---|
| **1** | **Secrets in `.env`** | Real AI provider API credentials | Plaintext `./.env` file at root read by unauthorized local users or background utilities. | Credential compromise, unauthorized API usage, billing spikes. | Store strictly at root `./.env` (outside `data/`); disclose plaintext trade-off; apply OS file permissions (Windows NTFS ACLs / Linux chmod); load via backend only; no UI key storage; document provider-side revocation. | `DEC-003`; `CONFIG_AND_SECRETS_SPEC.md` | `ACC-003`; File permission check |
| **2** | **Accidental Git Exposure** | Developer `./.env`, SQLite DB (`data/illum.db`), run logs, exports | User runs `git add .` or `git commit -a`, staging local credentials or local project data. | Public or repository-wide leak of operational keys and unpublished stories. | Comprehensive `.gitignore` covering `.env`, `.env.*` (except `.env.example`), `data/`, `*.db`, `exports/`, `logs/`, `tmp/`. Example template `.env.example` contains placeholders only. | `DEC-003`; `CONFIG_AND_SECRETS_SPEC.md` | `ACC-002` (Sentinel Git Scan) |
| **3** | **Keys in UI / Bundles / Logs** | API credentials, Bearer tokens, HTTP headers | Frontend Vite bundle packages backend env vars, or unhandled exceptions log headers or echo secrets to UI console. | Secrets visible in browser developer tools or persistent disk log files. | Strict backend isolation (FastAPI proxy only; zero keys in frontend); exception handlers sanitize errors; UI shows masked state (`••••1234`) and status only. | `DEC-003`; `PRODUCT_RULES_AND_INVARIANTS.md` | Bundle grep; exception trace inspection |
| **4** | **Provider Payload Leakage** | Unpublished video scripts, prompt templates | Raw JSON request/response payloads logged to stdout or saved in unhandled debug traces on failure. | Intellectual property leak, exposure of draft storylines in crash reports. | Logger configured to INFO/WARN without HTTP payload dump; error handler maps failures to normalized codes (`SchemaInvalid`, `RateLimited`) without raw echoing. | `DEC-018`; `PRODUCT_RULES_AND_INVARIANTS.md` | Log assertion tests with mock provider |
| **5** | **Database Prompt Persistence** | User source text, draft stories, full LLM prompts | Execution history table persists raw prompt strings, source text, or raw completion payloads long after task completion. | Data privacy violation, forensic recovery of discarded drafts, database bloat. | Strict DEC-018 invariant: schema strictly limited to operational metadata columns; schema validation forbids raw prompt/source/payload columns or text blobs. | `DEC-018`; `DATA_MODEL_AND_RELATIONSHIPS.md` | `ACC-030B` (DB schema reflection) |
| **6** | **History Retention & FIFO** | SQLite storage capacity, query performance | Generation records accumulate indefinitely, causing database degradation and violating retention agreements. | Uncontrolled database growth, slow query times, non-compliance with approved baseline. | Enforce DEC-018: hard cap of 100 records per project; insertion of 101st record executes immediate FIFO deletion of oldest record for that project. | `DEC-018`; `JOBS_USAGE_HISTORY_SPEC.md` | `ACC-030A` (100-Record FIFO test) |
| **7** | **Project Deletion Cleanup** | User privacy, orphaned database rows, orphaned disk files | Deleting a project removes the root row but leaves orphaned execution history, outputs, or temp files on disk. | Lingering user data, ghost records, storage bloat, potential cross-project ID confusion. | Two-phase staged deletion with quarantine and SQLite `ON DELETE CASCADE`. Verifies target is strictly inside `data/projects/`. | `DEC-018`, `DEC-019`; `EXPORT_DELETE_SECURITY_SPEC.md` | `ACC-032` (Project deletion test) |
| **8** | **Export ZIP Secret Inclusion** | `.env` file, database file, local log dumps | Project export ZIP recursively packages root directory or hidden files, leaking `./.env` or application logs into export archive. | User shares project ZIP with collaborators, inadvertently distributing active API credentials. | Whitelist-only archive builder (strictly `script.json`, prompts, SEO, settings); scans final ZIP manifest to verify `.env`, `*.db`, and secrets are 100% excluded. | `DEC-003`; `EXPORT_DELETE_SECURITY_SPEC.md` | `ACC-031` (ZIP manifest scan) |
| **9** | **Temporary Files & Scratchpads** | In-progress script generations, candidate scratchpads | Job fails or server crashes during generation, leaving half-written files in temp folders. | Disk clutter, stale candidate leakage, unvalidated outputs mistakenly displayed to user. | Write temporary files to project-scoped `tmp/` with unique job IDs; purge on job finish/fail/cancel; preserve existing validated script until new candidate validates. | `PRODUCT_RULES_AND_INVARIANTS.md`; `JOBS_USAGE_HISTORY_SPEC.md` | Post-job filesystem assertion scan |
| **10** | **Cross-Project Isolation** | Project isolation, distinct settings and aspect ratios | API routes or queries take `project_id` without strict isolation, allowing Project A to read or overwrite Project B. | Data corruption, accidental script replacement across projects, tenant leakage. | Strict non-mutating UUID v4 validation; safe path containment via `is_relative_to`; mandatory `WHERE project_id = :id` on all queries; composite cache keys. | `DATA_MODEL_AND_RELATIONSHIPS.md` | `ACC-007` (Cross-tenant isolation) |
| **11** | **External Provider Boundaries** | User trust, unintended network egress, rate limits | Application silently falls back to alternate provider on failure or contacts Module E endpoints without user consent. | Unintended network calls, quota exhaustion, unexpected model behavior, non-compliance with terms. | Strict no-silent-switch rule (primary failure halts and asks explicit user permission before alternate model); Module E connectors execute only on explicit user click. | `DEC-007` (OPEN), `DEC-010`; `PROVIDER_MODEL_MANAGER_SPEC.md` | `ACC-025` (Failover consent test) |
| **12** | **Shared `.env` Protection** | System-wide provider credentials at `./.env` | Project deletion, 5th-project replacement (DEC-019), or retention pruning deletes or mutates the shared `./.env` file. | Configured API keys destroyed, breaking all other projects and disrupting application operation. | Invariant: `./.env` is stored at application root outside `data/`; project deletion services strictly target `data/projects/{project_id}` and project DB tables; `./.env` path is immutable. | `DEC-003`, `DEC-018`, `DEC-019`; `PRODUCT_RULES_AND_INVARIANTS.md` | `ACC-032` (`.env` hash check after delete) |

---

## 3. Canonical `.env` Location & Boundary Isolation

### Authoritative Path:
```text
ai-studio/
├── app/
├── migrations/
├── tests/
├── docs/
├── data/                    # local data directory; ignored by Git
│   ├── illum.db             # SQLite database file
│   └── projects/            # Individual project directories ({project_id}/)
├── exports/                 # local exports; ignored by Git
├── logs/                    # local logs; ignored by Git
├── .env.example             # Placeholder variable template
├── .env                     # AUTHORITATIVE SHARED CREDENTIAL FILE (Root Level)
├── .gitignore
├── requirements.txt
├── run.bat
└── README.md
```

- **Location:** The shared `.env` file resides strictly at the **application root directory (`./.env`)**.
- **Isolation Guarantee:** It is permanently outside the `data/` directory where individual projects, SQLite database tables, and project assets reside. Deletion and cleanup services operate strictly within `data/projects/` and cannot traverse to or mutate the root `./.env` file.

---

## 4. Two-Phase Project Replacement Protocol (DEC-019)

### 1. Architectural Principle
The old project database row and its cascaded execution history are **never deleted** until the new project directory is staged, promoted, and completely verified on disk. If any failure occurs during filesystem operations, the original 4 projects remain 100% intact in both database and filesystem.

### 2. State Machine & Canonical Journal Stages
The replacement transaction is governed by the `replacement_journal` table:
```sql
CREATE TABLE replacement_journal (
    replacement_id TEXT PRIMARY KEY,
    old_project_id TEXT NOT NULL,
    new_project_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

#### Canonical Stages:
1. `INITIATED` — User clicked YES on confirmation prompt; global mutex acquired.
2. `OLD_LOCKED` — `P_old.status = 'REPLACING_LOCKED'` persisted in SQLite.
3. `NEW_REGISTERED` — `P_new.status = 'STAGING'` inserted in SQLite.
4. `NEW_STAGED` — `data/projects/{new_id}.tmp/` written, flushed, and validated on disk.
5. `OLD_QUARANTINING` — Journal committed immediately before old directory rename.
6. `OLD_QUARANTINED` — Atomic rename completed: `data/projects/{old_id}/` -> `data/projects/{old_id}.quarantine/`.
7. `NEW_PROMOTING` — Journal committed immediately before new directory promotion.
8. `NEW_PROMOTED` — Atomic rename completed: `data/projects/{new_id}.tmp/` -> `data/projects/{new_id}/`, disk verification passed.
9. `FINAL_COMMITTED` — Single atomic SQLite transaction commits: `DELETE old_id`, `P_new.status = 'ACTIVE'`, journal updated.
10. `PURGING_QUARANTINE` — Journal committed immediately before deleting `{old_id}.quarantine/`.
11. `COMPLETED` — Quarantined directory purged; journal closed; mutex released.
12. `ABORTED` — Rollback executed; original 4 projects active; staging purged; journal closed.

### 3. Active Project Counting Invariant
- Active project count is strictly:
  ```sql
  SELECT COUNT(*) FROM projects WHERE status = 'ACTIVE';
  ```
- During replacement:
  - `P_old` is `REPLACING_LOCKED` (not active).
  - `P_new` is `STAGING` (not active).
  - Active count is strictly **3** (never exceeds 4).
  - Total database rows is **5** temporarily, resolving to **4** upon `FINAL_COMMITTED`.
  - Quarantined (`*.quarantine`) and staging (`*.tmp`) directories are ignored by all project enumeration endpoints.

---

## 5. Exhaustive Crash-Window Decision Table

| Crash Window | State at Crash | SQLite DB State (`old` / `new`) | Disk Reality (`old_dir` / `old_quarantine` / `new_tmp` / `new_dir`) | Recovery Strategy | Exact Recovery Actions | Resulting Active Projects |
|---|---|---|---|---|---|---|
| **W1: Staged, Pre-Quarantine** | `NEW_STAGED` committed | `old`: `REPLACING_LOCKED`<br>`new`: `STAGING` | `old_dir`: Present<br>`old_quarantine`: None<br>`new_tmp`: Present<br>`new_dir`: None | **Roll Back** | 1. Purge `new_tmp/`.<br>2. `BEGIN IMMEDIATE; DELETE FROM projects WHERE id = :new_id; UPDATE projects SET status = 'ACTIVE' WHERE id = :old_id; UPDATE replacement_journal SET stage = 'ABORTED'; COMMIT;` | 4 original projects `ACTIVE`. |
| **W2: Pre-Quarantine Rename** | `OLD_QUARANTINING` committed | `old`: `REPLACING_LOCKED`<br>`new`: `STAGING` | `old_dir`: Present<br>`old_quarantine`: None<br>`new_tmp`: Present<br>`new_dir`: None | **Roll Back** | 1. Purge `new_tmp/`.<br>2. Execute atomic rollback transaction (restore `P_old: ACTIVE`, delete `P_new`, mark `ABORTED`). | 4 original projects `ACTIVE`. |
| **W3: Mid-Quarantine Rename** | Crash during `os.rename(old, quarantine)` | `old`: `REPLACING_LOCKED`<br>`new`: `STAGING` | Same-volume rename is atomic in OS namespace: either `old_dir` exists OR `old_quarantine` exists. | **Roll Back** | 1. Purge `new_tmp/`.<br>2. If `old_quarantine` exists, rename `old_quarantine` -> `old_dir`.<br>3. Execute atomic rollback transaction. | 4 original projects `ACTIVE`. |
| **W4: Post-Quarantine, Pre-Journal** | Rename done; crash before `OLD_QUARANTINED` write | `old`: `REPLACING_LOCKED`<br>`new`: `STAGING` | `old_dir`: Missing<br>`old_quarantine`: Present<br>`new_tmp`: Present<br>`new_dir`: None | **Roll Back** | 1. Purge `new_tmp/`.<br>2. Rename `old_quarantine` -> `old_dir`.<br>3. Execute atomic rollback transaction. | 4 original projects `ACTIVE`. |
| **W5: Pre-Promotion Rename** | `NEW_PROMOTING` committed | `old`: `REPLACING_LOCKED`<br>`new`: `STAGING` | `old_dir`: Missing<br>`old_quarantine`: Present<br>`new_tmp`: Present<br>`new_dir`: None | **Roll Back** | 1. Purge `new_tmp/`.<br>2. Rename `old_quarantine` -> `old_dir`.<br>3. Execute atomic rollback transaction. | 4 original projects `ACTIVE`. |
| **W6: Mid-Promotion Rename** | Crash during `os.rename(new_tmp, new_dir)` | `old`: `REPLACING_LOCKED`<br>`new`: `STAGING` | Atomic pointer swap: either `new_tmp` exists OR `new_dir` exists. | **Roll Back** | 1. Purge whichever exists (`new_tmp/` or `new_dir/`).<br>2. Rename `old_quarantine` -> `old_dir`.<br>3. Execute atomic rollback transaction. | 4 original projects `ACTIVE`. |
| **W7: Post-Promotion, Pre-Journal** | Promotion done; crash before `NEW_PROMOTED` write | `old`: `REPLACING_LOCKED`<br>`new`: `STAGING` | `old_dir`: Missing<br>`old_quarantine`: Present<br>`new_tmp`: Missing<br>`new_dir`: Present | **Roll Back** | DB swap not committed; `P_old` is authoritative. Purge `new_dir/`; rename `old_quarantine` -> `old_dir`; execute atomic rollback transaction. | 4 original projects `ACTIVE`. |
| **W8: Pre-Final SQLite Commit** | `NEW_PROMOTED` verified; crash before `COMMIT;` | `old`: `REPLACING_LOCKED`<br>`new`: `STAGING` | `old_quarantine`: Present<br>`new_dir`: Present | **Roll Back** | DB auto-rolled back uncommitted TX. Purge `new_dir/`; rename `old_quarantine` -> `old_dir`; execute atomic rollback transaction. | 4 original projects `ACTIVE`. |
| **W9: Post-Final SQLite Commit** | `FINAL_COMMITTED` committed; crash before purge | `old`: Missing<br>`new`: `ACTIVE` | `old_quarantine`: Present<br>`new_dir`: Present | **Roll Forward** | DB commit succeeded. `P_new` is legally active. Purge `old_quarantine/`; mark journal `COMPLETED`. | Exactly 4 projects (`P_new` active, `P_old` deleted). |
| **W10: Mid-Quarantine Purge** | `PURGING_QUARANTINE` (Crash during file deletion) | `old`: Missing<br>`new`: `ACTIVE` | `old_quarantine`: Partially deleted<br>`new_dir`: Present | **Roll Forward** | DB commit succeeded. Complete deletion of residual `old_quarantine/`; mark journal `COMPLETED`. | Exactly 4 projects (`P_new` active, `P_old` deleted). |
| **W11: Recovery Crash** | Crash during any recovery step above | Matches one of discrete states W1–W10 | Idempotent recovery operations | **Idempotent Retry** | Re-running recovery at startup evaluates physical disk + DB and re-executes cleanly. | Deterministic 4 projects. |
| **W12: Contradictory State** | e.g. Both `old_dir` and `old_quarantine` missing; unparseable foreign directories | Any inconsistent DB state | Unresolvable missing or conflicting folders | **SAFE BLOCKED STATE** | **HALT**. Never delete anything. Mark project `CORRUPTED_LOCKED`. Emit alert; block mutations. | No silent deletion; data preserved. |

---

## 6. Recovery-of-Recovery (Crashes during Startup Recovery)

| Recovery Interruption Point | State Immediately Prior to Interruption | Physical State upon Subsequent Startup Restart | Reconciled Determination | Subsequent Recovery Action | Final System State |
|---|---|---|---|---|---|
| **Crash during R1: Staging Purge** | In rollback; deleting `new_tmp/` files | DB: `P_old: REPLACING_LOCKED`, `P_new: STAGING`<br>Disk: `new_tmp/` partially deleted; `old_dir/` intact | Journal stage is prior to `FINAL_COMMITTED`; `old_dir/` intact; `new_tmp/` is uncommitted garbage. | Re-invoke idempotent purge on `new_tmp/`. Proceed to R2/R3. | 4 original projects `ACTIVE`. |
| **Crash after R2: Old Dir Restored** | `old_quarantine/` renamed to `old_dir/`; crash before DB update | DB: `P_old: REPLACING_LOCKED`, `P_new: STAGING`<br>Disk: `old_dir/` intact; `old_quarantine/` gone; `new_tmp/` gone | `old_dir/` is fully restored; DB update was interrupted. | 1. `old_dir/` verified intact; skip filesystem rename.<br>2. Execute atomic rollback transaction (`DELETE P_new`, `P_old: ACTIVE`, mark `ABORTED`). | 4 original projects `ACTIVE`. |
| **Crash before / after writing `ABORTED`** | Writing journal `stage = 'ABORTED'` | DB: 4 `ACTIVE` projects; journal `ABORTED` (or unwritten) | Disk and DB already clean. | If journal unwritten, write `ABORTED`. If already `ABORTED`, do nothing. | 4 original projects `ACTIVE`. |
| **Crash during F1: Roll-Forward Quarantine Purge** | In roll-forward; deleting `old_quarantine/` files | DB: `P_new: ACTIVE`, `P_old` deleted<br>Disk: `new_dir/` active; `old_quarantine/` partially purged | `FINAL_COMMITTED` was committed in DB. `P_new` is active. Residual quarantine files are garbage. | 1. Re-invoke safe purge on `old_quarantine/`.<br>2. `UPDATE replacement_journal SET stage = 'COMPLETED';` | Exactly 4 projects (`P_new` active, `P_old` deleted). |
| **Conflicting / Unresolvable State** | Disk folders missing or unverified foreign paths detected | Any inconsistent DB state | Mismatch cannot be proven safe | **FAIL CLOSED**: Do not delete any directory. Set status `CORRUPTED_LOCKED`. Emit diagnostic alert. | Data preserved; mutations blocked. |

---

## 7. Cross-Process Concurrency & Single-Instance Enforcement

1. **Durable File Lock (`data/.app.lock`):**
   - At startup, before opening SQLite or inspecting disk, the process must acquire an exclusive, non-blocking OS file lock on `data/.app.lock`:
     - **Windows:** `msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)` or `win32file.LockFileEx`.
     - **POSIX:** `fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)`.
   - **Enforcement:** If lock acquisition fails, the secondary process halts immediately with error:
     `"Another instance of ILLUM AI Studio is actively using this data directory. Exiting."`
2. **SQLite Cross-Process Concurrency (`BEGIN EXCLUSIVE`):**
   - All project creation, deletion, replacement, and startup-recovery database transactions must use `BEGIN EXCLUSIVE TRANSACTION;`.
   - Acquires an OS-level write lock on the database file, guaranteeing that no other thread or process can access SQLite during the critical section.
3. **DEC-019 Serialization:**
   - Under `BEGIN EXCLUSIVE`, the count query `SELECT COUNT(*) FROM projects WHERE status = 'ACTIVE'` and the creation/replacement operations are fully serialized, making concurrent over-creation impossible.

---

## 8. Operating System Filesystem Sandboxing & Safe Deletion

### 1. POSIX Directory-Handle Deletion (`dir_fd`)
On POSIX platforms (Linux, macOS), file-descriptor-relative traversal eliminates path-resolution race conditions:

```python
import os
import stat

def safe_purge_directory_posix(parent_dir_fd: int, dir_name: str) -> None:
    # 1. Open subdirectory descriptor with O_NOFOLLOW and O_DIRECTORY
    sub_fd = os.open(
        dir_name, 
        os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW, 
        dir_fd=parent_dir_fd
    )
    
    try:
        # 2. fstat() identity verification on the opened descriptor
        sub_stat = os.fstat(sub_fd)
        if not stat.S_ISDIR(sub_stat.st_mode):
            raise SecurityException("Opened descriptor is not a valid directory")
            
        # 3. Mount-point boundary check (compare st_dev against parent)
        parent_stat = os.fstat(parent_dir_fd)
        if sub_stat.st_dev != parent_stat.st_dev:
            raise SecurityException("Mount-point crossing detected; traversal halted")
            
        # 4. Descriptor-based bottom-up directory iteration
        with os.scandir(sub_fd) as it:
            for entry in it:
                if entry.is_symlink():
                    os.unlink(entry.name, dir_fd=sub_fd)
                elif entry.is_dir(follow_symlinks=False):
                    safe_purge_directory_posix(sub_fd, entry.name)
                else:
                    os.unlink(entry.name, dir_fd=sub_fd)
                    
    finally:
        os.close(sub_fd)
        
    # 5. Remove empty directory relative to parent descriptor
    os.rmdir(dir_name, dir_fd=parent_dir_fd)
```

#### POSIX Limitation & Fail-Closed Requirement:
- Between `os.close(sub_fd)` and `os.rmdir(dir_name, dir_fd=parent_dir_fd)`, an external process could replace the empty directory.
- Before calling `os.rmdir()`, re-inspect `os.stat(dir_name, dir_fd=parent_dir_fd, follow_symlinks=False)` to assert `st_dev` and `st_ino` match `sub_stat` and `st_nlink == 2`.
- If any discrepancy occurs: **FAIL CLOSED**. Abort deletion; leave quarantine intact; mark project locked.

### 2. Windows 10/11 Safe Deletion & Fail-Closed Policy
- **Vulnerability:** Path-based traversal on Windows (`os.scandir` + `os.path.realpath` + `os.unlink`/`os.rmdir`) is vulnerable to TOCTOU races.
- **Native Handle Deletion:** True race-free deletion requires `CreateFileW` with `FILE_FLAG_OPEN_REPARSE_POINT` and setting `FileDispositionInfoEx` via `SetFileInformationByHandle`.
- **Pure Python Limitation:** Pure Python standard library on Windows **does not expose** handle-based file unlinking without native bindings.
- **Mandatory Fail-Closed Policy:**
  - Ordinary path validation is **never claimed as an equivalent security guarantee**.
  - If native Win32 handle-bound deletion is absent:
    1. Check junctions (`os.path.isjunction` / `entry.is_junction()` in Python 3.12+), symlinks (`entry.is_symlink()`), and reparse tags (`FILE_ATTRIBUTE_REPARSE_POINT`).
    2. If an entry cannot be removed cleanly, or if an unexpected reparse point is detected, or if a sharing violation occurs (`ERROR_SHARING_VIOLATION` / `WinError 32`), **abort destructive deletion immediately**.
    3. Retain the directory in `.quarantine`; mark project `LOCKED`; log non-destructive alert for startup recovery.

---

## 9. Non-Mutating Canonical UUID v4 Validation Specification

### Vulnerability of Standard `uuid.UUID(..., version=4)`:
Python's standard library `uuid.UUID(val, version=4)` constructor mutates version and variant bits rather than rejecting invalid UUIDs. To strictly validate UUID v4 without mutation:

```python
import uuid
import re

# Strict RFC 4122 Section 4.4 pattern: exactly 36 chars, lowercase hex, hyphens at 8-4-4-4-12
UUID_V4_EXACT_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z"
)

def validate_canonical_uuid_v4(val: object) -> str:
    # 1. Reject non-string input
    if not isinstance(val, str):
        raise TypeError(f"Project ID must be a string, got {type(val).__name__}")
        
    # 2. Exact length and regex match (no strip() — whitespace causes rejection)
    if len(val) != 36 or not UUID_V4_EXACT_REGEX.match(val):
        raise ValueError("Project ID must be an exact canonical lowercase RFC 4122 UUID v4")
        
    # 3. Parse WITHOUT version argument to prevent bit mutation
    try:
        parsed = uuid.UUID(val)
    except (ValueError, AttributeError):
        raise ValueError("Malformed UUID structure")
        
    # 4. Explicit structural assertions
    if parsed.version != 4:
        raise ValueError(f"Expected UUID version 4, got version {parsed.version}")
    if parsed.variant != uuid.RFC_4122:
        raise ValueError("UUID variant must be RFC 4122")
    if str(parsed) != val:
        raise ValueError("UUID string is not in canonical representation")
        
    return val
```

---

## 10. Durability Specification & Failure Limitations

### 1. Nested Staging Flush Ordering
1. **Leaf Files:** Write data -> `f.flush()` -> `os.fsync(f.fileno())` -> `f.close()`.
2. **Subdirectories:** Open directory descriptor -> `os.fsync(dir_fd)` -> `os.close(dir_fd)`.
3. **Staging Root Directory:** Open descriptor for `{new_id}.tmp/` -> `os.fsync(tmp_fd)` -> `os.close(tmp_fd)`.
4. **Parent Directory:** Call `os.fsync(parent_fd)` on `data/projects/`.
5. **Atomic Rename:** Execute `os.rename()` within the same volume.
6. **Parent Directory Post-Rename:** Call `os.fsync(parent_fd)` to persist directory entry mutation.
7. **SQLite WAL Commit:** Execute `COMMIT;` with `PRAGMA synchronous = FULL;`.

### 2. Durability Limitations
- **Covered:** Process termination (`SIGKILL`, unhandled exception), standard OS crashes where filesystem journal and SQLite WAL flush.
- **Uncovered (Hardware Boundaries):** Volatile write-back disk caching without power-loss protection (PLP); physical drive failure; unreadable bad sectors. Software cannot guarantee survival against unbuffered physical power interruption.

---

## 11. Governance & Evidence Status

- **`DEC-003`, `DEC-018`, `DEC-019`:** `APPROVED BASELINE AMENDMENTS` (Unchanged).
- **`DEC-007`:** `OPEN` (Google Gemini candidate 1, Groq alternate candidate; neither supported or verified).
- **`P00-T04` Task Status:** `IN PROGRESS (Security Blocker Resolved)`.
- **Runtime Security Tests:**
  - `ACC-002`: `PASSED` (Pre-coding security setup verified: root `.gitignore` excludes `.env`, `.env.*` except `.env.example`, `data/`, `logs/`, `tmp/`; sentinel secret verified absent from Git commit history via `git status --ignored` and `git log -p`).
  - `ACC-003`: `BLOCKED / NOT RUN` (Runtime missing config behavior belongs to P01 implementation; application code deferred).
- **Subsequent Tasks:** `P00-T05` and `P01` are `NOT STARTED`.
