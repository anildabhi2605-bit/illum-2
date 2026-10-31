# AI Studio — Complete Requirements & Build Pack

**Purpose:** Is ZIP ko implementation ke waqt single navigation point ke roop mein use karein. Iska goal hai ki developer ko sirf `Phase ID` aur `Task ID` dekar us task ka scope, dependencies, file deliverables, rules, tests aur done criteria clear mil sake.

## Is pack ka status

- **Documentation pack:** Prepared in this delivery.
- **Application source code / working app:** Is pack se verify nahi hua; implementation status `NOT STARTED / NOT VERIFIED` maana jayega jab tak repository aur test evidence attach na ho.
- **Authoritative original product plan:** `99_REFERENCE_SOURCE/01_MASTER_PLAN_APPROVED_ORIGINAL.md`.
- **Prior detailed explanation:** `99_REFERENCE_SOURCE/02_DETAILED_MASTER_PLAN_HINGLISH.md`.
- **Prior sequencing roadmap:** `99_REFERENCE_SOURCE/03_BUILD_ORDER_ROADMAP_EXISTING.md`.
- **Original complete skill prompts:** Current provided source mein nahi the; Phase `P00` mein authoritative copies import karni hain.
- **Original `09_TEST_AND_ACCEPTANCE_MATRIX.md`:** Source plan mein referenced hai, lekin is delivery ke input files mein separately supplied nahi tha. `05_TESTING/ACCEPTANCE_MATRIX_PROPOSED.md` proposed working matrix hai, original file ka substitute tab tak nahi maana jayega jab tak authoritative matrix verify/import na ho.

## Start here — exact order

1. Read `01_BASELINE/PRODUCT_RULES_AND_INVARIANTS.md`.
2. Read `07_CHANGE_CONTROL/DECISION_REGISTER.md` and reconcile approved plan plus user-requested local deployment and Idea Research additions.
3. Read `02_ARCHITECTURE/MASTER_ARCHITECTURE.md`.
4. Read `04_BUILD_TASKS/PHASE_INDEX.md`.
5. Work strictly in `P00` → `P15` order. Task files are in `04_BUILD_TASKS/tasks/`.
6. A phase must not start until the previous phase's exit gate has evidence.
7. Update `07_CHANGE_CONTROL/IMPLEMENTATION_STATUS.md` after every task; do not mark a task done without test output, commit/PR or equivalent evidence.

## Core product decisions carried into the build plan

- Local-first Python application installed from GitHub; user can manage provider keys in a local `.env` using Notepad for developer/local mode.
- Four original skills remain separate and preserve protected contracts.
- Optional Module E, Idea Research & Discovery, is a pre-source route; it must not replace direct manual source entry.
- Research connectors are modular; no connector is described as supported until implemented and tested.
- Local `.env` is plain text and is not equivalent to encrypted server-side secret storage. This is an explicit local-mode security trade-off and must be documented/tested.
- A later Windows executable is an optional release target, not an initial prerequisite.

## Task invocation format

Give a build agent this request shape:

> Implement **P05-T02 — First real provider adapter**. First read `README_START_HERE.md`, the product invariants, the architecture docs and this exact task file. Inspect repository state; do not assume earlier tasks passed. Implement only this task and prerequisites already completed. Run all listed tests. Update task status and evidence. Do not start subsequent tasks. If a required original prompt, credential, endpoint, API access or decision is missing, record a blocker rather than inventing it.

## Strict phase rule

No skipping ahead. If a later phase is needed to test a lower-level component, add a temporary focused test only; do not build the later feature early. If any new requirement changes the baseline, record it in `DECISION_REGISTER.md` before implementation.


## Detailed build inventory

- Phases: 16 (`P00`–`P15`).
- Individually specified tasks: 83; see `04_BUILD_TASKS/TASK_INDEX.md`.
- Every task file contains goal, prerequisites, source inputs, step-by-step work, deliverables, acceptance criteria, tests, prohibited shortcuts, blocker rules, and definition of done.
- Use `00_START_HERE/INDEX.md` to navigate the documentation pack.
