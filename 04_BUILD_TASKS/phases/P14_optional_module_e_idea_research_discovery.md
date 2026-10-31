# P14 — Optional Module E — Idea Research & Discovery

**Phase intent:** Add evidence-backed research as an optional pre-source route, never as a requirement for manual source entry.

**Exit gate:** Connectors truthfully report status; ranking/dossier/import and partial-failure cases pass; direct source flow stays intact.

## Tasks (strict order)

### [P14-T01] Freeze research scope, connectors and ranking policy
- **Goal:** Define Module E's first release before implementation.
- **Prerequisites:** P13 core acceptance passed; DEC-010 recorded.
- **Deliverables:** Research design record and versioned rank formula.
- **Acceptance:** No full-internet claim; supported source list explicit; ranking weights and limitations documented.

### [P14-T02] Create research connector interface and status model
- **Goal:** Standardize adapters while keeping each source independent.
- **Prerequisites:** P14-T01; P05 provider patterns.
- **Deliverables:** Research connector interface and mocks.
- **Acceptance:** Unavailable connector truthfully reports status; one connector failure does not imply total failure.

### [P14-T03] Implement Trends connector with replaceable adapter
- **Goal:** Gather trend signals through supported official means where available; keep PyTrends experimental.
- **Prerequisites:** P14-T02; source-access policy.
- **Deliverables:** Trends adapter(s) and capability notes.
- **Acceptance:** Signal source and limits explicit; no absolute search volume invented; experimental adapter failures handled.

### [P14-T04] Implement news and web article discovery/fetch
- **Goal:** Collect recent news/article results and accessible content for topics.
- **Prerequisites:** P14-T02; source access policy.
- **Deliverables:** News/web adapters.
- **Acceptance:** No article content fabricated; publication and retrieval times distinguishable; inaccessible text is marked.

### [P14-T05] Implement keyword suggestions path
- **Goal:** Support keywords without misrepresenting free website access as free API.
- **Prerequisites:** P14-T02; DEC-013 resolved.
- **Deliverables:** Keyword suggestions adapter/manual-reference flow.
- **Acceptance:** Free website not treated as free unlimited API; unavailable metrics shown as Unknown.

### [P14-T06] Implement optional X and Reddit adapters
- **Goal:** Add public discussion discovery where access is actually configured and allowed.
- **Prerequisites:** P14-T02; official API access/terms verified.
- **Deliverables:** Separate X/Reddit adapters.
- **Acceptance:** Only tested/authorized access shown as available; absent credentials produce honest partial coverage.

### [P14-T07] Normalize, deduplicate, cluster and rank candidates
- **Goal:** Turn raw connector results into up to four explainably ranked topics.
- **Prerequisites:** P14-T03–T06 as applicable; P14-T01 ranking formula.
- **Deliverables:** Normalization/ranking service and candidate schema.
- **Acceptance:** No fake ranks/filler; up to four; signal and confidence are separate; scope and score formula shown.

### [P14-T08] Generate detailed dossier and user-confirmed source import
- **Goal:** Research selected topic into a source-supported main-story dossier, then optional source-panel import.
- **Prerequisites:** P14-T07; P05/P06/P07/P08/P09 services available.
- **Deliverables:** Research dossier UI/service and explicit source import route.
- **Acceptance:** Every factual claim is traceable where possible; no full-text claim from snippets; no auto-start to script; manual source route remains.

### [P14-T09] Run Module E acceptance and regression tests
- **Goal:** Verify optional research is resilient and does not affect Skills A-D.
- **Prerequisites:** P14-T01–T08.
- **Deliverables:** Module E acceptance report and release decision.
- **Acceptance:** Research can be disabled without affecting manual source workflow; scores/citations/status truthful; no core regression.

## Phase rule
Complete tasks in listed order. If a prerequisite or source artifact is absent, mark the affected task BLOCKED and do not pretend its acceptance tests passed. The phase is done only when every required task is verified and the exit gate has evidence.
