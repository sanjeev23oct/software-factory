---
name: build-tasks
description: Build every unticked task of a work item with a maker and an independent checker, writing evidence for each gate.
---
# build-tasks

Work through `<spec folder>/tasks.md` from the first unticked box. You are the harness: you dispatch makers and checkers and you write no feature code yourself.

For each section:

1. **Maker.** For each unticked task, start a subagent with the skill the task names and the task's lines from `tasks.md`. One task, one maker.
2. **Checker.** When the section's tasks are built, start a fresh subagent that has not seen the maker's work. It runs the gate: every Cat 1 check in `loop/*-checker.md` against its EXPECTED value, then the Cat 3 command. It writes the evidence file the gate names, as a table of check, expected, actual, result, with a first line `Status: PASS` or `Status: FAIL`.
3. **Tick** the section's boxes only when the evidence says PASS. On FAIL, send the findings to a maker, then check again. Stop after three failed attempts on one section and report it.

Rules:

- A maker never runs the gate and never writes evidence. A checker never edits feature code.
- Never tick a box with a note that the check was skipped or deferred.
- Never invent a detail the spec does not give. Stop and report it.
- If `factory_feedback.md` exists, the factory's own evidence check rejected the last attempt. Fix every finding in it first.

When you finish, a script re-reads the evidence and re-runs the Cat 1 checks itself.
