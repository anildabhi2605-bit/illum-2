# Task Execution Contract — Mandatory for Every Phase/Task

When asked to build a task by ID, follow this sequence exactly.

1. **Load context:** read Start Here, invariants, master architecture, relevant feature spec, exact task file and decision register.
2. **Inspect actual repo:** verify files/commits and status. Do not assume a previous task was completed because the plan says so.
3. **Check prerequisites:** collect test evidence for dependencies. If missing/failing, stop and report blocker.
4. **State scope internally and in task report:** implement only that task and prerequisite repair explicitly approved by the user. Do not begin the next task.
5. **Inspect existing patterns:** reuse the project architecture; do not invent a second stack or duplicative module.
6. **Implement:** smallest coherent change satisfying all task acceptance criteria and preserving invariants.
7. **Test:** run task tests plus regression tests relevant to changed components. Do not claim tests not executed.
8. **Security review:** check secrets, project isolation, data retention and failure paths where relevant.
9. **Evidence:** record commands, result, changed files, commit/PR or exact evidence path, and unresolved concerns.
10. **Update status board and changelog.** Mark `VERIFIED` only when required evidence exists; otherwise use `IMPLEMENTED`, `BLOCKED` or `IN PROGRESS`.
11. **Stop at exit gate.** Do not start later tasks automatically.

## Per-task output format

- Task ID and title
- Initial repository state
- Requirements interpreted from source docs
- Files/modules changed
- Design decisions and why
- Tests run and exact outcomes
- Acceptance criteria checklist
- Security and regression impact
- Status and evidence location
- Remaining blockers
- Next permitted task ID (not automatically implemented)

## Non-negotiable

Never silently change a protected skill contract, add an unapproved feature, claim untested support, fabricate source coverage/cost/progress, expose secrets, or remove user data before safe deletion is confirmed.
