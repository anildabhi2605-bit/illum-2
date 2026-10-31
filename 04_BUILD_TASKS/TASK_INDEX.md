# Task Index — Give a Phase ID + Task ID to Build One Defined Unit

Each task has a dedicated file in `tasks/`. Work strictly in phase order; dependencies and exit gates override convenience. All statuses initially NOT STARTED / NOT VERIFIED.

| Phase | Task ID | Task title | Prerequisite / gate | Task file |
|---|---|---|---|---|
| P00 | P00-T01 | Import authoritative product artifacts | None. This is the first task. | [Open](tasks/P00-T01.md) |
| P00 | P00-T02 | Reconcile requested amendments into baseline | P00-T01 artifact inventory available. | [Open](tasks/P00-T02.md) |
| P00 | P00-T03 | Choose and record the technology stack | P00-T02. | [Open](tasks/P00-T03.md) |
| P00 | P00-T04 | Freeze connector, credentials and retention boundaries | P00-T02; P00-T03 where stack needed. | [Open](tasks/P00-T04.md) |
| P00 | P00-T05 | Baseline acceptance tests and phase gates | P00-T01 through P00-T04. | [Open](tasks/P00-T05.md) |
| P01 | P01-T01 | Create repository skeleton | P00 complete. | [Open](tasks/P01-T01.md) |
| P01 | P01-T02 | Pin dependencies and developer commands | P01-T01. | [Open](tasks/P01-T02.md) |
| P01 | P01-T03 | Implement local runtime entrypoint | P01-T01; P01-T02. | [Open](tasks/P01-T03.md) |
| P01 | P01-T04 | Set up test runner, linting and logging baseline | P01-T01; P01-T02. | [Open](tasks/P01-T04.md) |
| P01 | P01-T05 | Write clean-install smoke procedure | P01-T01 through P01-T04. | [Open](tasks/P01-T05.md) |
| P02 | P02-T01 | Implement typed configuration loading | P01 complete; P00 decisions. | [Open](tasks/P02-T01.md) |
| P02 | P02-T02 | Harden repository ignore rules and example config | P01-T01; P02-T01. | [Open](tasks/P02-T02.md) |
| P02 | P02-T03 | Implement key add/remove and restart semantics | P02-T01; P02-T02. | [Open](tasks/P02-T03.md) |
| P02 | P02-T04 | Implement provider connection test boundary | P02-T01; provider interface may be stubbed until P05. | [Open](tasks/P02-T04.md) |
| P02 | P02-T05 | Run configuration security acceptance tests | P02-T01–T04. | [Open](tasks/P02-T05.md) |
| P03 | P03-T01 | Define domain entities and state enums | P01 complete; P00 baseline. | [Open](tasks/P03-T01.md) |
| P03 | P03-T02 | Implement database schema and migrations | P03-T01; stack decision. | [Open](tasks/P03-T02.md) |
| P03 | P03-T03 | Implement project-scoped repositories | P03-T02. | [Open](tasks/P03-T03.md) |
| P03 | P03-T04 | Implement local files and temporary-data service | P03-T02; P02 secret rules. | [Open](tasks/P03-T04.md) |
| P03 | P03-T05 | Verify migrations, persistence and isolation | P03-T01–T04. | [Open](tasks/P03-T05.md) |
| P04 | P04-T01 | Implement project create/list/open lifecycle | P03 complete. | [Open](tasks/P04-T01.md) |
| P04 | P04-T02 | Build settings form and ratio/language rules | P04-T01; P03-T01. | [Open](tasks/P04-T02.md) |
| P04 | P04-T03 | Implement exact duration/part calculator | P04-T02. | [Open](tasks/P04-T03.md) |
| P04 | P04-T04 | Enforce four-project active limit transactionally | P04-T01; P03-T02. | [Open](tasks/P04-T04.md) |
| P04 | P04-T05 | Test project/settings UX states | P04-T01–T04. | [Open](tasks/P04-T05.md) |
| P05 | P05-T01 | Define provider adapter interface and mock | P02/P03 complete. | [Open](tasks/P05-T01.md) |
| P05 | P05-T02 | Implement the first real provider adapter | P05-T01; P00-T04 provider decision; valid credential/access. | [Open](tasks/P05-T02.md) |
| P05 | P05-T03 | Implement model catalog and capability metadata | P05-T02. | [Open](tasks/P05-T03.md) |
| P05 | P05-T04 | Implement project-preferred routing and user-approved fallback | P05-T01–T03. | [Open](tasks/P05-T04.md) |
| P05 | P05-T05 | Validate provider responses and classify retries | P05-T01–T04. | [Open](tasks/P05-T05.md) |
| P05 | P05-T06 | Run provider adapter acceptance suite | P05-T01–T05. | [Open](tasks/P05-T06.md) |
| P06 | P06-T01 | Implement job state machine and progress | P05 interface; P03 job model. | [Open](tasks/P06-T01.md) |
| P06 | P06-T02 | Prevent duplicate jobs and handle idempotency | P06-T01; P03 constraints. | [Open](tasks/P06-T02.md) |
| P06 | P06-T03 | Implement safe retries and cancellation handling | P06-T01/T02; P05-T05. | [Open](tasks/P06-T03.md) |
| P06 | P06-T04 | Track execution history and usage honestly | P06-T01; P05 adapter response. | [Open](tasks/P06-T04.md) |
| P06 | P06-T05 | Build jobs/history UI and failure messages | P06-T01–T04. | [Open](tasks/P06-T05.md) |
| P07 | P07-T01 | Implement source-version repository/model | P03/P04 complete. | [Open](tasks/P07-T01.md) |
| P07 | P07-T02 | Build Source Adding Panel UI and status actions | P07-T01; UI spec. | [Open](tasks/P07-T02.md) |
| P07 | P07-T03 | Implement source readability/content validation | P07-T01/T02; HTTP reader capability decision. | [Open](tasks/P07-T03.md) |
| P07 | P07-T04 | Connect source edits to invalidation hooks | P07-T01/T03; P08 may provide shared invalidation contract. | [Open](tasks/P07-T04.md) |
| P07 | P07-T05 | Verify source workflow acceptance | P07-T01–T04. | [Open](tasks/P07-T05.md) |
| P08 | P08-T01 | Implement reusable analysis cache keyed by inputs | P07 complete; P03 analysis model. | [Open](tasks/P08-T01.md) |
| P08 | P08-T02 | Implement dependency invalidation engine | P08-T01; P07-T04. | [Open](tasks/P08-T02.md) |
| P08 | P08-T03 | Implement latest-script candidate replacement transaction | P08-T02; script storage schema. | [Open](tasks/P08-T03.md) |
| P08 | P08-T04 | Enforce approval hash/settings gate on backend | P08-T02/T03. | [Open](tasks/P08-T04.md) |
| P08 | P08-T05 | Build approval and stale-state UI | P08-T01–T04. | [Open](tasks/P08-T05.md) |
| P08 | P08-T06 | Run version, analysis and approval matrix | P08-T01–T05. | [Open](tasks/P08-T06.md) |
| P09 | P09-T01 | Bind Skill A original contract to use case | P00-T01 complete; P05/P06/P07/P08 exit gates passed. | [Open](tasks/P09-T01.md) |
| P09 | P09-T02 | Generate and reuse Source Analysis | P09-T01; P08-T01. | [Open](tasks/P09-T02.md) |
| P09 | P09-T03 | Implement fact-grounded script generation | P09-T01/T02; P05/P06. | [Open](tasks/P09-T03.md) |
| P09 | P09-T04 | Implement script/duration validation and targeted correction | P09-T03; P04 duration service. | [Open](tasks/P09-T04.md) |
| P09 | P09-T05 | Complete Skill A review/approval end-to-end test | P09-T01–T04 and P08 exit. | [Open](tasks/P09-T05.md) |
| P10 | P10-T01 | Wire Skill B input and approval gate | P09 complete; P08 approved gate. | [Open](tasks/P10-T01.md) |
| P10 | P10-T02 | Generate per-part video prompts | P10-T01; P05/P06. | [Open](tasks/P10-T02.md) |
| P10 | P10-T03 | Validate and persist Skill B outputs | P10-T02; P08 invalidation. | [Open](tasks/P10-T03.md) |
| P10 | P10-T04 | Run Skill B acceptance suite | P10-T01–T03. | [Open](tasks/P10-T04.md) |
| P11 | P11-T01 | Wire thumbnail skill to entire current approved script | P09/P08 complete; original Skill C imported. | [Open](tasks/P11-T01.md) |
| P11 | P11-T02 | Generate exactly one complete thumbnail prompt | P11-T01; provider/job services. | [Open](tasks/P11-T02.md) |
| P11 | P11-T03 | Validate and stale-mark thumbnail output | P11-T02; P08 invalidation engine. | [Open](tasks/P11-T03.md) |
| P11 | P11-T04 | Run Skill C acceptance suite | P11-T01–T03. | [Open](tasks/P11-T04.md) |
| P12 | P12-T01 | Define SEO result schema and Roman Hindi validation | P09/P08 complete; original Skill D imported. | [Open](tasks/P12-T01.md) |
| P12 | P12-T02 | Generate project-aware SEO package | P12-T01; provider/job manager; approval policy. | [Open](tasks/P12-T02.md) |
| P12 | P12-T03 | Validate, save and invalidate SEO output | P12-T02; P08 invalidation. | [Open](tasks/P12-T03.md) |
| P12 | P12-T04 | Run Skill D acceptance suite | P12-T01–T03. | [Open](tasks/P12-T04.md) |
| P13 | P13-T01 | Implement data-only project ZIP export | P09–P12; data model stable. | [Open](tasks/P13-T01.md) |
| P13 | P13-T02 | Implement safe project deletion and cleanup | P03/P04; cleanup service. | [Open](tasks/P13-T02.md) |
| P13 | P13-T03 | Run security and project-isolation review | P02–P13 artifacts. | [Open](tasks/P13-T03.md) |
| P13 | P13-T04 | Run core full end-to-end acceptance | P09–P13 prior tasks. | [Open](tasks/P13-T04.md) |
| P13 | P13-T05 | Finalize retention, diagnostics and backup notes | P06/P13-T01–T03. | [Open](tasks/P13-T05.md) |
| P14 | P14-T01 | Freeze research scope, connectors and ranking policy | P13 core acceptance passed; DEC-010 recorded. | [Open](tasks/P14-T01.md) |
| P14 | P14-T02 | Create research connector interface and status model | P14-T01; P05 provider patterns. | [Open](tasks/P14-T02.md) |
| P14 | P14-T03 | Implement Trends connector with replaceable adapter | P14-T02; source-access policy. | [Open](tasks/P14-T03.md) |
| P14 | P14-T04 | Implement news and web article discovery/fetch | P14-T02; source access policy. | [Open](tasks/P14-T04.md) |
| P14 | P14-T05 | Implement keyword suggestions path | P14-T02; DEC-013 resolved. | [Open](tasks/P14-T05.md) |
| P14 | P14-T06 | Implement optional X and Reddit adapters | P14-T02; official API access/terms verified. | [Open](tasks/P14-T06.md) |
| P14 | P14-T07 | Normalize, deduplicate, cluster and rank candidates | P14-T03–T06 as applicable; P14-T01 ranking formula. | [Open](tasks/P14-T07.md) |
| P14 | P14-T08 | Generate detailed dossier and user-confirmed source import | P14-T07; P05/P06/P07/P08/P09 services available. | [Open](tasks/P14-T08.md) |
| P14 | P14-T09 | Run Module E acceptance and regression tests | P14-T01–T08. | [Open](tasks/P14-T09.md) |
| P15 | P15-T01 | Run full regression and clean-install validation | P13 accepted; P14 accepted if included. | [Open](tasks/P15-T01.md) |
| P15 | P15-T02 | Verify update and migration procedure | P15-T01; migration plan. | [Open](tasks/P15-T02.md) |
| P15 | P15-T03 | Build optional Windows executable | P15-T01; packaging decision approved. | [Open](tasks/P15-T03.md) |
| P15 | P15-T04 | Define release/update and rollback procedure | P15-T01/T02; optional P15-T03. | [Open](tasks/P15-T04.md) |
| P15 | P15-T05 | Publish release evidence and close milestone | P15-T01–T04. | [Open](tasks/P15-T05.md) |
