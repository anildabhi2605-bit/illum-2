# P01 — Repository skeleton and repeatable Python runtime

**Phase intent:** Create the minimal application shell and a repeatable setup before adding product logic.

**Exit gate:** A fresh clone can create an isolated environment, install pinned dependencies, start the local app, execute tests and stop cleanly.

## Tasks (strict order)

### [P01-T01] Create repository skeleton
- **Goal:** Build clean modules and folders with clear separation of UI, domain, services, providers, skills and tests.
- **Prerequisites:** P00 complete.
- **Deliverables:** Initial repo structure and module import tests.
- **Acceptance:** Package imports without circular dependencies; no secrets/user data in repository; boundaries match architecture.

### [P01-T02] Pin dependencies and developer commands
- **Goal:** Make installation repeatable on supported Python versions.
- **Prerequisites:** P01-T01.
- **Deliverables:** Pinned dependency definition and setup instructions.
- **Acceptance:** Fresh venv can install without relying on globally installed packages; dependencies are intentional and documented.

### [P01-T03] Implement local runtime entrypoint
- **Goal:** Create repeatable startup/shutdown and bind the UI to localhost by default.
- **Prerequisites:** P01-T01; P01-T02.
- **Deliverables:** `run` command/script and stable startup behavior.
- **Acceptance:** App starts/stops on supported environment; no accidental LAN exposure; failure messages are actionable.

### [P01-T04] Set up test runner, linting and logging baseline
- **Goal:** Provide test command and safe structured logging before functional code grows.
- **Prerequisites:** P01-T01; P01-T02.
- **Deliverables:** Working test runner and logging foundation.
- **Acceptance:** A simple test passes/fails deterministically; logs contain no config values by default.

### [P01-T05] Write clean-install smoke procedure
- **Goal:** Document and test local setup from a clean checkout.
- **Prerequisites:** P01-T01 through P01-T04.
- **Deliverables:** README install section and clean-install evidence.
- **Acceptance:** New developer can follow instructions without relying on undocumented local state.

## Phase rule
Complete tasks in listed order. If a prerequisite or source artifact is absent, mark the affected task BLOCKED and do not pretend its acceptance tests passed. The phase is done only when every required task is verified and the exit gate has evidence.
