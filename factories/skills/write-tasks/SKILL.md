---
name: write-tasks
description: Write tasks.md and the checker files for a work item: every task names the skill that fits it, every section ends in a gate, and maker and checker are separate.
---
# write-tasks

Write `<spec folder>/tasks.md` and `<spec folder>/loop/<section>-checker.md`. Write only inside the spec folder and change no code. The approved requirements, and the design when there is one, are the contract.

A script checks every rule below after you finish.

## Start the file by saying how it is built

The file opens with this note, so anyone reading it knows who does what:

```
> **Maker and checker.** Each task is built by a maker, using the skill named on the task.
> A checker then verifies the section in a separate session: it did not see the maker work,
> it runs the gate against what was built, and it alone writes the evidence.
> Nothing is ticked until the checker's evidence says PASS.
```

## Format

```
## Section 1 — Logic (`src/board.js`)

Satisfies: AC 1.1, AC 1.2, correctness property 2

- [ ] 1.1 `matchesSearch(task, search)` in `src/board.js`        → run: `/build-ui-logic`
  - [ ] 1.1.1 returns true when the lower-cased title contains the lower-cased search
- [ ] 1.2 `visibleTasks(tasks, filter, search)` in `src/board.js`  → run: `/build-ui-logic`

### 1.X — Gate

> **CHECKER (Cat 1):** every check in `loop/logic-checker.md` returns its EXPECTED value.
> **CHECKER (Cat 2):** write `evidence/1-logic-gate.md` as a tick sheet.
> **CHECKER (Cat 3):** run the tests for this section; EXPECTED: all pass.
```

## Choosing the skill for a task

The prompt lists the maker skills this route has and the files each is for. For every task:

- Name the file the task touches, in backticks, on the task line.
- Name the one skill that is for that file: `→ run: \`/skill\``. A script rejects a task whose file belongs to a different skill.
- If no skill fits, do not force one. List the task under `## Needs clarification`.

One task builds one thing with one skill. If a task needs two skills, it is two tasks.

## The related tasks a piece of work needs

Work is rarely one file. Give each kind of change its own section and its own tasks, in the order they build on each other.

For UI work, cover all of these that apply:

1. **Logic**: the functions that decide what is shown.
2. **View**: the markup, with exact text, every state (empty, error, nothing found), and `data-testid`s.
3. **Page**: the element in the page, the event wiring, the styles, keyboard and screen-reader labels.
4. **Sample data**: so every state can be seen.
5. **Tests**: for the logic and for the view.

For backend work: data or schema, then data access, then validation and endpoints, then tests, then the documentation of the interface.

Tests are always the last section and use the tests skill.

## Rules

- Every task (a checkbox numbered `N.M`) names a skill that exists on this route.
- Every section ends in a gate with Cat 1 (matches the spec), Cat 2 (the evidence file, named `evidence/<n>-<name>-gate.md`) and Cat 3 (it runs). A section titled Tests needs no gate of its own.
- Cat 1 checks go in `loop/<section>-checker.md` as shell commands, each followed by `# EXPECTED: <n>` or `# EXPECTED: at least <n>`. Prefer `grep -c` so a script can re-run them. Derive each expected value from the spec, not from code that does not exist yet.
- Say which acceptance criteria each section satisfies.
- All boxes start unticked.

If `factory_feedback.md` exists, a check rejected your last attempt. Fix every finding in it.
