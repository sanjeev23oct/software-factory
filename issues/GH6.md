---
title: Rename a task
author: sam
state: open
labels: agent:feature, area:cli, triaged, ready-to-spec, spec-in-review
---
If I make a typo in a task title the only fix is to rm it and add it again, which gives it a new id and loses the done state. I would like to change the title of an existing task in place.

---
**factory-triage** · 2026-10-09 02:30 UTC

Type: feature. This asks for a new capability (change a task's title in place), not a fix for wrong behavior.

**Confirmed the limitation** on a scratch `--db` file (no real data touched):

    add "tpyo"      -> added 1
    done 1          -> done 1
    rename 1 typo   -> exit 2, argparse: invalid choice: 'rename' (choose from 'add', 'list', 'done', 'rm')
    rm 1; add typo  -> list shows "[ ]   2  typo"

So the only workaround today does lose both the id and the done state, exactly as reported.

**Where it touches the code**
- `tasklite/cli.py:14-23` - the subparsers are `add`, `list`, `done`, `rm`; a new subcommand taking an id and a new title is needed here.
- `tasklite/cli.py:37-55` - command dispatch; the new branch should reuse the existing `TaskNotFound` -> `error: no task with id N` / exit 1 path (`tasklite/cli.py:53-55`).
- `tasklite/store.py:26-44` - `Store` has `add`, `complete`, `remove` and no title mutator. A new method can follow `complete` (`tasklite/store.py:38-41`): look the task up with `_find_index` and set `task["title"]`, leaving `id` and `done` untouched.
- `tasklite/store.py:27-28` - why the workaround loses state: `add` always takes a fresh `next_id` and sets `done` to `False`.
- No change to the task file format is needed: only the existing `title` field is rewritten, so old task files keep loading.
- Tests in `tests/test_store.py` and `tests/test_cli.py`, plus the README command list.

**Duplicate check:** not a duplicate. GH1 (`done` index bug, closed), GH2 (due dates), GH3 (vague no-repro), GH4 (sync) and GH5 (traceback on empty task file) describe different problems; none requests editing a title.

**No follow-up questions.** The need is clear and nothing is missing that only the reporter could supply.

**Recommendation: `ready-to-spec`.** The implementation is small, but the user-visible choices are open and should be settled first: the command name (`rename` vs `edit` vs `mv`), the success output text (e.g. `renamed 1`), and what happens with an empty or whitespace-only new title (note `add` currently accepts an empty title, so the spec should decide whether rename matches that or rejects it). If the maintainer is happy to pick `rename <id> <title>` printing `renamed <id>` directly, this could go straight to `ready-to-implement`.

Readiness recommendation for the maintainer: `ready-to-spec`

---
**maintainer** · 2026-10-09 02:30 UTC

Applied label `ready-to-spec`.

---
**factory-spec** · 2026-10-09 02:41 UTC

Related issue: GH6

Adds `specs/GH6/product.md` and `specs/GH6/tech.md` for a new `rename` command.

**Product spec.** `tasklite rename <id> <title>` changes a task's title in place and prints `renamed <id>`. The task keeps its id, done state and list position, and no id is consumed. The title is stored verbatim as a single argument. An unknown id gives the existing `error: no task with id <id>` on stderr with exit 1 and leaves the task file untouched. Usage errors behave as for the existing commands (exit 2). The task file format does not change.

**Tech spec.** One new `Store.rename(task_id, title)` method beside `complete`, one new subparser and one dispatch branch in `cli.py` reusing the shared `TaskNotFound` path. Lists the store and CLI test cases that prove each invariant. No README change: the README has no tasklite command list.

**Open questions for the maintainer**

1. Command name: the spec picks `rename` (the reporter's word). `edit` and `mv` were the alternatives raised in triage.
2. Empty or whitespace-only title: the spec accepts it and stores it as given, matching what `add` does today. The alternative is to reject it, either in `rename` only (the two commands would then disagree) or in both (wider than this issue).

**Note.** The unmerged `factory/GH5` branch edits the same `try`/`except` block in `cli.py`, so the implementation may hit a small textual conflict depending on merge order.

Specs: `specs/GH6/` on branch `factory/GH6`
