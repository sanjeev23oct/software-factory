---
title: `done` marks the wrong task after I delete one
author: priya
state: open
labels: triaged, bug, area:storage, repro:confirmed, ready-to-implement, in-review
---
I had three tasks. I removed the first one, then ran `done 3` and it said
"error: no task with id 3" even though `list` clearly shows task 3.

Then I ran `done 2` and it printed "done 3" and ticked off task 3 instead of 2!

Steps:

    python3 -m tasklite add "a"
    python3 -m tasklite add "b"
    python3 -m tasklite add "c"
    python3 -m tasklite rm 1
    python3 -m tasklite done 2
    python3 -m tasklite list

Expected task 2 to be checked. Task 3 is checked instead.

---
**factory-triage** · 2026-10-09 00:16 UTC

Confirmed. I reproduced the exact steps from the report with a scratch `--db` file (no real data touched):

    add a / add b / add c   -> ids 1,2,3
    rm 1                     -> removed 1; list shows "2 b", "3 c"
    done 2                   -> printed "done 3", and list now shows "2 b" (unchecked), "3 c" [x]

So the report is accurate: `done 2` ticks off task 3, not task 2.

Root cause: `Store.complete` (tasklite/store.py:32-37) resolves `task_id` as a **1-based index into the in-memory list** (`self.tasks[task_id - 1]`), not as a lookup by the task's `id` field:

    def complete(self, task_id):
        if task_id < 1 or task_id > len(self.tasks):
            raise TaskNotFound(task_id)
        task = self.tasks[task_id - 1]
        task["done"] = True
        return task

Because `self.tasks` is a plain list, removing an earlier task (`Store.remove`, tasklite/store.py:39-43, which — correctly — searches by `task["id"] == task_id`) shifts every later task's list position. After `rm 1`, the task with id 3 sits at index 1, so `complete(2)` grabs `self.tasks[1]`, which is task 3. This also explains the first symptom in the report: before the `rm`, there were 3 tasks, so `done 3` used index 2 — fine; but the reporter's transcript implies ordering issues consistent with this same index/id confusion as soon as the list is shorter than the max id.

Fix should make `complete` look up by `id` the same way `remove` does (e.g. factor out a shared `_find(task_id)` helper used by both), and a regression test should cover: add 3, remove an early one, then `done` on a surviving higher id, asserting the correct task (by id) is the one marked done and no other task is touched.

Not a duplicate: issues/GH2.md (due dates), GH3.md ("its broken", no repro), and GH4.md (sync) are unrelated.

Recommend `ready-to-implement`: bug reproduced, root cause pinpointed to a single function, fix is localized to `tasklite/store.py`.

Recommended readiness: `ready-to-implement`

---
**maintainer** · 2026-10-09 00:17 UTC

Applied label `ready-to-implement`.

---
**factory-implement** · 2026-10-09 00:19 UTC

Fixed GH1: `Store.complete(task_id)` was indexing into `self.tasks` by position (`task_id - 1`) instead of looking up the task by its `id` field. Since `Store.remove` correctly deletes by id (shifting later tasks' list positions), any `done <id>` call after an earlier removal would operate on the wrong task.

Fix: factored a shared `_find_index(task_id)` helper (searches by `id`, raises `TaskNotFound` if absent) and made both `complete` and `remove` use it, so `complete` now looks up tasks by their permanent id exactly like `remove` already did. No other files needed changes; task id permanence and file format were preserved.

Verified the regression tests fail against the original buggy code (reproduced `done 3` instead of `done 2`) and pass with the fix. Also manually reproduced the exact repro steps from the issue end-to-end via the CLI with a scratch db file and confirmed `done 2` now correctly marks task 2.

Branch: `factory/GH1`
