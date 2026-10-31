# Phase Index — Strict Build Order

## Important status note

All tasks below start as `NOT STARTED` unless implementation evidence is added. The documentation pack is prepared; the application build is not verified.

| Phase | Name | Depends on | Exit gate |
|---|---|---|---|
| P00 | Requirements, source contracts, change control | None | Original contracts and acceptance matrix located; all material decisions recorded |
| P01 | Repository skeleton and repeatable Python runtime | P00 | Clean environment can install/start; tests run |
| P02 | Configuration and secret safety | P01 | `.env` workflow and secret leak tests pass |
| P03 | Domain models, local DB and migrations | P01/P02 | Schema/migrations/isolation invariants pass |
| P04 | Project manager and settings | P03 | Settings/durations/project limit pass |
| P05 | Provider interface and first tested adapter | P02/P03 | Real adapter validated with safe tests; routing rules pass |
| P06 | Jobs, retry, usage, history | P05 | Job lifecycle, duplicate prevention and error handling pass |
| P07 | Source panel and validation | P03/P04/P06 | Saved/readable/validated source gates pass |
| P08 | Analysis reuse, stale invalidation and approval | P07 | Version and approval gates pass backend and UI tests |
| P09 | Skill A: Story-to-Script | P05/P06/P08 | Contract and duration/content tests pass |
| P10 | Skill B: Video Prompt | P09/P08 | Approval, per-part prompt and staleness tests pass |
| P11 | Skill C: Thumbnail Prompt | P09/P08 | One prompt, whole-script input, settings checks pass |
| P12 | Skill D: YouTube SEO | P09/P08 | Roman Hindi output and required fields pass |
| P13 | Export, deletion, security, core end-to-end acceptance | P09–P12 | Core acceptance and secret/data controls pass |
| P14 | Optional Module E: Idea Research | P13 | Connector status, ranking, dossier/import tests pass |
| P15 | Full regression, clean install, optional package/release | P13; P14 if included in release | Release acceptance evidence and rollback/update docs complete |

## Rule for blockers

If a task depends on a missing original skill prompt, acceptance test, provider access, API contract, or user decision, mark it `BLOCKED`. Do not invent a replacement and continue as though the dependency were satisfied.


## Phase document links

- [P00 — Requirements and baseline freeze](phases/P00_requirements_and_baseline_freeze.md)
- [P01 — Repository skeleton and repeatable Python runtime](phases/P01_repository_skeleton_and_repeatable_python_runtime.md)
- [P02 — Configuration and secret safety](phases/P02_configuration_and_secret_safety.md)
- [P03 — Domain models, local database and migrations](phases/P03_domain_models_local_database_and_migrations.md)
- [P04 — Project manager and project settings](phases/P04_project_manager_and_project_settings.md)
- [P05 — Provider interface and first tested adapter](phases/P05_provider_interface_and_first_tested_adapter.md)
- [P06 — Jobs, retries, usage and execution history](phases/P06_jobs_retries_usage_and_execution_history.md)
- [P07 — Source Adding Panel and validation](phases/P07_source_adding_panel_and_validation.md)
- [P08 — Analysis reuse, invalidation and approval gates](phases/P08_analysis_reuse_invalidation_and_approval_gates.md)
- [P09 — Skill A — Story-to-Script](phases/P09_skill_a_story_to_script.md)
- [P10 — Skill B — Script-to-Video Prompt Engineering](phases/P10_skill_b_script_to_video_prompt_engineering.md)
- [P11 — Skill C — Thumbnail Intelligence](phases/P11_skill_c_thumbnail_intelligence.md)
- [P12 — Skill D — YouTube SEO](phases/P12_skill_d_youtube_seo.md)
- [P13 — Export, deletion, security and core integration acceptance](phases/P13_export_deletion_security_and_core_integration_acceptance.md)
- [P14 — Optional Module E — Idea Research & Discovery](phases/P14_optional_module_e_idea_research_discovery.md)
- [P15 — Regression, installation, packaging and release](phases/P15_regression_installation_packaging_and_release.md)

For the complete individual task list, see [TASK_INDEX.md](TASK_INDEX.md). Each ID has its own task specification file.
