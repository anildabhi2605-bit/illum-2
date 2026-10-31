# Module E — Idea Research & Discovery Engine (Optional Pre-Source Module)

## Status

User-requested scope addition for planning. Implement only after the four core skills, source/approval foundation, and core acceptance tests are stable. This module does not replace manual source entry.

## User journey

1. User opens Idea Research from a project or creates a research run.
2. Selects geography, time window, niche/topic filter, language/query behavior and enabled source connectors.
3. App shows connector readiness; unavailable connectors are not silently treated as scanned.
4. Collects results in parallel where safe and permitted.
5. Normalizes timestamps/source metadata, deduplicates and groups related terms/articles into candidate topics.
6. Ranks evidence-backed candidates; show up to four, not necessarily four.
7. User selects a topic.
8. App performs deeper targeted research and creates a structured dossier.
9. User reviews citations, timeline, conflicts and evidence confidence.
10. User explicitly chooses to import dossier into existing Source Panel, edits if needed, saves and validates.
11. Only then does Skill A become available.

## Source connector policy

Potential connectors: Google Trends (supported official means when available; RSS/CSV where applicable), experimental PyTrends (unofficial/archived; replaceable), Keyword Tool (manual free site vs separate paid API), Google News, web/article search, X, Reddit. Each is an adapter with credentials, terms/rate limits, timeouts, normalized errors and status.

No connector should be marked Supported until implemented and tested. Access, region, rate limits and pricing must be current-verified at implementation time. Never promise complete worldwide internet coverage.

## Ranking principles

Keep two different dimensions:

- **Trend/momentum score:** relative popularity, change over time, recency, cross-source presence, keyword signals.
- **Evidence confidence:** independent credible source support, primary-source availability, corroboration and unresolved conflicts.

Exact weights are not established in the original plan; choose and document them in P14 before release. Display short ranking reasons, actual signal timestamp and connectors searched. Do not fabricate volume, sample size, rank or coverage.

## Detailed dossier sections

Executive summary; background; verified timeline; key factual claims with citations; latest developments; entities; trends/keywords; news coverage; social signals clearly labelled as unverified opinions until corroborated; conflicting accounts; confidence/evidence gaps; possible truthful story angles; references with URL/title/publication and retrieval time.

## Safety/quality rules

- Trend != truth.
- A social post is a lead, not automatically verified evidence.
- Preserve contradictory reports and uncertainty.
- If only snippets/headlines are accessible, do not claim full-article reading.
- No results/partial connector coverage should be stated explicitly.
- Cache/reuse only according to approved freshness policy; research reruns should not silently overwrite a previously valid dossier.
- Search data should be normalized and deduplicated; repeated reposts should not masquerade as independent corroboration.
- Import is user-controlled; no automatic source replacement or script generation.

## Acceptance tests

Up to four evidence-backed candidates; fewer when warranted; transparent connector status; deduplication; score/confidence separate; report citations clickable; missing/limited source access honest; import confirmation; source panel validation still required; manual direct-source route unaffected; secrets not logged/exported.
