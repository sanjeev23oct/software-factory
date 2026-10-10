---
name: write-tasks
description: Write tasks.md and the checker files for a work item: every task names a skill, every section ends in a gate.
---
# write-tasks

Write `<spec folder>/tasks.md` and `<spec folder>/loop/<section>-checker.md`. Write only inside the spec folder and change no code. The approved requirements, and the design when there is one, are the contract.

A script checks every rule below after you finish.

## Format

```
## Section 1 — Backend

- [ ] 1.1 `OrderDto` and `CreateOrderDto`              → run: `/build-backend`
  - [ ] 1.1.1 fields exactly per design.md § API
- [ ] 1.2 `POST /api/orders`                           → run: `/build-backend`

### 1.X — Gate

> **CHECKER (Cat 1):** every check in `loop/backend-checker.md` returns its EXPECTED value.
> **CHECKER (Cat 2):** write `evidence/1-backend-gate.md` as a tick sheet.
> **CHECKER (Cat 3):** run the tests for this section; EXPECTED: all pass.
```

## Rules

- Every task (a checkbox numbered `N.M`) names the skill that builds it: `→ run: \`/skill\``. Use a skill that exists in this factory's skills folder or the repository's `.claude/skills/`. If no skill fits a task, list it under `## Needs clarification` instead of leaving it bare.
- Order sections so each builds on the last: data, then backend, then UI, then tests.
- Every section ends in a gate with Cat 1 (matches the spec), Cat 2 (evidence file, named `evidence/<n>-<name>-gate.md`) and Cat 3 (it runs). A section titled Tests needs no gate.
- Cat 1 checks go in `loop/<section>-checker.md` as shell commands, each followed by `# EXPECTED: <n>` or `# EXPECTED: at least <n>`. Prefer `grep -c` so a script can run them.
- Map each section to the acceptance criteria it satisfies.
- All boxes start unticked.

If `factory_feedback.md` exists, a check rejected your last attempt. Fix every finding in it.
