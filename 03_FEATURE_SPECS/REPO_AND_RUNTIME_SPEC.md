# Repository and Local Runtime Specification

## Proposed initial deployment

- Local-first Python application cloned/downloaded from GitHub.
- Starts on the user's computer; UI is bound to localhost by default (not exposed to the LAN unless explicitly configured and documented).
- Local data directory for database, caches, exports and logs; directories containing user data are ignored by Git.
- Internet remains required for configured external AI/search APIs.
- A later `.exe` or platform package is optional, after clean-install and regression gates.

## Proposed repository

```text
ai-studio/
  app/
    ui/
    use_cases/
    domain/
    persistence/
    providers/
    jobs/
    skills/
    research/
    security/
  migrations/
  tests/{unit,integration,acceptance}/
  docs/
  scripts/
  data/       # local-only
  exports/    # local-only
  logs/       # local-only
  .env.example
  .gitignore
  pyproject.toml or requirements.txt
  run.bat
  README.md
```

## Phase 0 stack decisions required

Record chosen UI framework, database (SQLite is a reasonable local-first candidate, but must be confirmed), ORM/migration approach, test runner, HTTP client, structured output validation method, configuration loader, provider SDK strategy, packaging tool and supported OS/Python versions. Do not introduce multiple frameworks when one satisfies requirements.

## Runtime responsibilities

- Check supported Python version, required config and local data directory.
- Give actionable startup errors if dependencies/configuration are missing.
- Run database migrations safely on startup or through a documented explicit command.
- Bind UI to localhost by default.
- Support clean shutdown and avoid leaving duplicate app instances/jobs where feasible.
- Provide a reproducible setup and test command.

## Installation lifecycle

1. Install Git + supported Python version.
2. Clone repository.
3. Create virtual environment.
4. Install locked/pinned dependencies.
5. Copy `.env.example` to `.env`.
6. Edit `.env` in Notepad and save valid provider credentials.
7. Run DB migrations/setup.
8. Launch app.
9. Test provider connection in UI or CLI.
10. Run test suite before updates/releases.

Exact command lines are to be committed only after the actual package/framework choice is made in P00.
