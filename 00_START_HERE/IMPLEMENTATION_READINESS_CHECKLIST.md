# Implementation Readiness Checklist

Use this before starting P01 and again before the first release.

## Must be ready before coding skill logic

- [ ] Original approved master plan present and preserved.
- [ ] Exact original protected prompts for Skills A–D imported with provenance/version.
- [ ] Original `09_TEST_AND_ACCEPTANCE_MATRIX.md` imported and compared; proposed matrix remains labelled proposed until reconciled.
- [ ] Requested local Python deployment and `.env` security trade-off recorded in the decision register.
- [ ] Optional Module E scope recorded; manual source route remains independent.
- [ ] Python/OS/UI/database/migration/test framework chosen and documented.
- [ ] First provider adapter selection justified by real access/capabilities; no provider assumed supported.
- [ ] Project/data paths, localhost binding and secret threat boundary approved.
- [ ] Task statuses initialized honestly; no unverified code marked complete.
- [ ] Requirement-to-test traceability exists.

## Must pass before Skill A

- [ ] Local app can start in a clean environment.
- [ ] Config and secret handling tests pass.
- [ ] Database migrations and project isolation tests pass.
- [ ] Project settings and duration tests pass.
- [ ] Provider adapter contract and response validation tests pass.
- [ ] Job state/retry/history baseline passes.
- [ ] Source is saved/validated and URL failure is handled honestly.
- [ ] Analysis cache, candidate replacement and backend approval gate are tested.

## Must pass before core release

- [ ] Skills A–D contracts pass separately.
- [ ] Source/script/settings invalidation suite passes.
- [ ] No silent model fallback; bounded retry verified.
- [ ] Four-project limit/deletion safety verified (DEC-019).
- [ ] Project export includes required artifacts and excludes secrets.
- [ ] Logs/diagnostics are redacted; local `.env` plainly documented as plaintext.
- [ ] Cross-project isolation test passes.
- [ ] Core acceptance and clean-install tests pass.

## Must pass before Module E release

- [ ] Connector access/cost/terms checked at build time.
- [ ] Each connector has separate capability/status and failure tests.
- [ ] Ranking formula is documented, versioned and explainable.
- [ ] Trend score and evidence confidence remain separate.
- [ ] Dossier citations and retrieval timestamps tested.
- [ ] Research import requires user confirmation and Source Panel validation.
- [ ] Core manual source workflow regression passes.

## Must pass before `.exe` release

- [ ] Source-based clean install is already stable.
- [ ] Build runs on the target OS; package does not include `.env` or secrets.
- [ ] User data and editable config are stored outside immutable bundle where possible.
- [ ] Upgrade/migration procedure tested.
- [ ] Release artifact hash and test evidence recorded.
