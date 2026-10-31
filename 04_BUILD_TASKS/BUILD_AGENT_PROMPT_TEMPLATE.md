# Build-Agent Prompt Template — Use One Task ID at a Time

Copy and fill the bracketed fields when asking an AI coding agent or developer to implement a task.

```text
You are implementing the AI Studio requirements pack. Follow the original master plan and all approved invariants strictly.

TASK ID: [e.g. P05-T02]
TASK FILE: 04_BUILD_TASKS/tasks/[TASK-ID].md
CURRENT REPOSITORY: [repo path/branch/commit]
TASK STATUS BOARD: 07_CHANGE_CONTROL/IMPLEMENTATION_STATUS.md

Mandatory actions:
1. Read 00_START_HERE/README_START_HERE.md and 01_BASELINE/PRODUCT_RULES_AND_INVARIANTS.md.
2. Read 02_ARCHITECTURE/MASTER_ARCHITECTURE.md and the feature spec relevant to this task.
3. Read the entire task file, decision register and prior task evidence.
4. Inspect the actual repository. Do not assume the plan proves a feature exists.
5. Verify prerequisites from actual test evidence. If missing, report BLOCKED rather than skipping phases.
6. Implement only this task and explicitly approved prerequisite repair. Do not start the next task.
7. Preserve the original Skill A-D contracts. Do not invent a missing contract or acceptance test.
8. Respect the local .env security limitations; never expose secrets in logs, UI, Git or exports.
9. Run every test listed in the task file and relevant regression tests. Report commands and actual results; do not claim unrun tests passed.
10. Update implementation status, change log and evidence paths.

Return:
- Task ID and status
- Initial repository state
- Requirements and decisions applied
- Files changed
- Design/implementation notes
- Tests run with results
- Acceptance checklist
- Security and regression findings
- Blockers/limitations
- Evidence/commit/PR
- Next permitted task ID (do not implement it)

Do not silently add features, change skill prompts, change durations/languages, add restore/import, switch models without permission, or mark unsupported providers as supported.
```
