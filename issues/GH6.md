---
title: Rename a task
author: sam
state: open
labels: agent:feature, area:cli, triaged
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
