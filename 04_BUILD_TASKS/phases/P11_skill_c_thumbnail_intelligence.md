# P11 — Skill C — Thumbnail Intelligence

**Phase intent:** Add thumbnail prompt generation from whole current approved script.

**Exit gate:** Exactly one complete prompt is validated, stored and invalidated correctly.

## Tasks (strict order)

### [P11-T01] Wire thumbnail skill to entire current approved script
- **Goal:** Ensure full script, not only hook, is the primary input.
- **Prerequisites:** P09/P08 complete; original Skill C imported.
- **Deliverables:** Skill C input orchestrator.
- **Acceptance:** Input contains whole current script and current settings; old script version rejected.

### [P11-T02] Generate exactly one complete thumbnail prompt
- **Goal:** Implement requested thumbnail prompt generation.
- **Prerequisites:** P11-T01; provider/job services.
- **Deliverables:** Thumbnail prompt generation.
- **Acceptance:** Exactly one complete prompt; no misleading visual claims; image itself is not generated.

### [P11-T03] Validate and stale-mark thumbnail output
- **Goal:** Tie prompt validity to current script/settings.
- **Prerequisites:** P11-T02; P08 invalidation engine.
- **Deliverables:** Thumbnail output persistence/invalidation.
- **Acceptance:** One current prompt per project; old prompt not presented as current after dependency change.

### [P11-T04] Run Skill C acceptance suite
- **Goal:** Verify whole-script dependency and exactly-one output.
- **Prerequisites:** P11-T01–T03.
- **Deliverables:** Skill C acceptance evidence.
- **Acceptance:** All contract rules pass and source evidence recorded.

## Phase rule
Complete tasks in listed order. If a prerequisite or source artifact is absent, mark the affected task BLOCKED and do not pretend its acceptance tests passed. The phase is done only when every required task is verified and the exit gate has evidence.
