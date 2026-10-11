---
name: check-tasks
description: Checker: in a separate session from the maker, verify one built section against the spec, write its evidence, and tick it only if it passes.
---
# check-tasks (the checker)

You are the checker. You run in a different session from the maker and did not see it work. Judge only what is in the checkout. Do not change any code.

The prompt names one section of `<spec folder>/tasks.md`.

## Verify

1. Read the requirements, the design if there is one, and the section's tasks with every sub-item.
2. Read what the maker built: `git log --oneline -5` and `git show --stat HEAD`, then the changed files themselves.
3. **Cat 1, matches the spec.** Run every command for this section in `<spec folder>/loop/*-checker.md` and compare each result with its `# EXPECTED` value. Then check each task's sub-items against the code by reading it.
4. **Cat 3, it works.** Run the command the section's gate names (usually the tests) and read the result.
5. Check that each task was built the way its named skill says, and that nothing was changed that no task asked for.

## Write the evidence (Cat 2)

Write the file the gate names, `<spec folder>/evidence/<n>-<name>-gate.md`:

```
Status: PASS

# Evidence: section 2, view

| Check | Expected | Found | Result |
| --- | --- | --- | --- |
| grep -c 'data-testid="search"' index.html | 1 | 1 | PASS |
| node --test | all pass | 11 pass, 0 fail | PASS |
```

The first line is exactly `Status: PASS` or `Status: FAIL`. Every row is something you ran or read yourself in this session, with what you actually found. Never copy a result from the maker's report.

## Decide

- **Everything passed:** tick this section's boxes in `tasks.md`, changing `[ ]` to `[x]` and nothing else.
- **Anything failed:** tick nothing. Write `factory_feedback.md` at the checkout root: each finding, the file and line, and what the maker must do. If a check in `loop/` is itself wrong, say so there.

You may write only under `evidence/`, tick boxes in `tasks.md`, and write `factory_feedback.md`. The factory rejects a checker that changes anything else, and it stamps your evidence with both session ids.
