---
title: Due dates for tasks
author: marco
state: open
labels: triaged, feature, area:cli, ready-to-implement, changes-requested
---
I'd like to give a task a due date when I add it, and be able to see what is
overdue. Right now I keep the dates in the title ("pay rent - 1st") which
means I can't filter on them.

Something like `add "pay rent" --due 2026-11-01` and a way to list only the
overdue ones would cover what I need. It would also be nice to see the due
date in the normal list.

---
**factory-triage** · 2026-10-09 00:17 UTC

Type: feature. This is a request for due dates on tasks, not a defect — nothing to reproduce.

Where it touches the code:
- `tasklite/store.py:27` — `Store.add(title)` builds the task dict with only `id`, `title`, `done`. A `due` field would need to be added here (and stay optional/`None` for old rows, since AGENTS.md requires existing task files to keep loading — `tasklite/store.py:16-20` blindly trusts `data["tasks"]`, so backward compat is a real constraint, not hypothetical).
- `tasklite/cli.py:14-15` — the `add` subparser only takes `title`; it would need a `--due` option, presumably validated/parsed as `YYYY-MM-DD`.
- `tasklite/cli.py:28-30` — `format_task` only prints `[x] id title`; showing the due date in normal `list` output means changing this formatter.
- `tasklite/cli.py:17` — `list` has no filtering; "overdue" would be either a new flag (`list --overdue`) or a new subcommand, and "overdue" needs a definition (due date < today, based on what clock/timezone).

Duplicate check: not a duplicate. `issues/GH1.md` is an unrelated `done`-indexing bug, `issues/GH3.md` is a no-repro vague complaint, `issues/GH4.md` is a different feature (cross-machine sync).

Why `ready-to-spec` rather than `ready-to-implement`: the problem is well articulated (stop stuffing dates into titles, be able to filter/see overdue), but the design has open questions a spec should pin down before coding — exact flag name/date format, precise definition of "overdue" (relative to what clock/timezone), whether undated tasks sort/display differently, and how old task files without `due` behave on load/save. Recommend writing `specs/GH2/product.md` + `tech.md` to settle those, then implement.

Recommended readiness: `ready-to-spec`

---
**maintainer** · 2026-10-09 00:17 UTC

Applied label `ready-to-spec`.

---
**factory-spec** · 2026-10-09 00:38 UTC

Wrote specs/GH2/product.md and specs/GH2/tech.md for issue GH2 (due dates for tasks).

Product spec defines 7 testable invariants: `add TITLE --due YYYY-MM-DD` sets a due date; `add` without `--due` is unchanged; strict `YYYY-MM-DD` validation with `error: invalid due date '<value>'` on bad input; `list` appends `  due YYYY-MM-DD` to a task's line when present and shows nothing extra otherwise; `list --overdue` shows only tasks with a due date before today that are not done; empty `--overdue` output is not an error; and pre-GH2 task files (no `due` key) load fine, display with no due text, and are never overdue. Out of scope: editing/clearing due dates after creation, sorting by due date, relative dates/times/recurrence, reminders, timezone configuration.

Tech spec maps each invariant to store.py/cli.py changes: Store.add gains a due=None parameter stored as a plain ISO string (no date-object parsing needed, since validated ISO-8601 strings sort correctly as strings — stated as the rejected alternative); a new pure is_overdue(task, today) helper in store.py using .get("due") for backward compatibility with old files; cli.py gains --due (validated via regex + strptime, raising ValueError caught alongside TaskNotFound to keep the "error: <message>"/exit-1 convention instead of argparse's own exit-2 validation) and --overdue on list; format_task appends due text only when present. Testing section lists concrete test cases per invariant in tests/test_cli.py and tests/test_store.py, using dates far in the past/future (year 2000/2999) to avoid clock mocking, plus a hand-written old-shape JSON file to prove backward compatibility. No manual verification steps required.

Specs: `.factory/worktrees/GH2/specs/GH2`

Open questions:
- Invariant 3: flag name `--due` and strict format `YYYY-MM-DD` — maintainer may prefer a different flag or more flexible date parsing.
- Invariant 4: due date shown as plain appended text `  due YYYY-MM-DD` — maintainer may prefer a different list layout.
- Invariant 5: "today" is the local system date with no timezone configuration — maintainer may want this configurable.
- Invariant 5: a done task is never considered overdue even if its due date passed — maintainer may want done tasks to still count as overdue until some other action clears them.

---
**maintainer** · 2026-10-09 00:39 UTC

Applied label `ready-to-implement`.

---
**factory-implement** · 2026-10-09 00:40 UTC

Implemented GH2 (due dates for tasks) per specs/GH2/product.md and tech.md. Added `due=None` parameter to `Store.add` (task dict now includes "due", defaulting to None so old files without the key still load via `.get`), and a pure `is_overdue(task, today)` helper in store.py using string comparison on validated ISO-8601 dates. In cli.py: added `--due` to the `add` subparser (plain string, not argparse-typed) with a new `parse_due(value)` helper that validates `YYYY-MM-DD` shape via regex then confirms it's a real calendar date via `strptime`, raising `ValueError("invalid due date '<value>'")` on failure — caught in `main` alongside `TaskNotFound` to produce `error: <message>` on stderr with exit code 1. Added `--overdue` flag to the `list` subparser; `main`'s list branch computes today's date and filters tasks through `is_overdue` when the flag is set. `format_task` now appends `  due YYYY-MM-DD` when a task has a due date, leaving undated tasks' output unchanged.

Branch: `factory/GH2`

---
**factory-review** · 2026-10-09 00:42 UTC

Review round 1: **approve**

GH2 implements due dates for tasks exactly per specs/GH2/product.md and tech.md. Store.add gains an optional due=None param stored as a plain validated ISO string; a pure is_overdue(task, today) helper uses .get("due") so pre-GH2 files without the key load and are never overdue. CLI adds --due (validated via regex+strptime, raising ValueError → "error: invalid due date '<value>'", exit 1) and --overdue on list; format_task appends "  due YYYY-MM-DD" only when present, leaving undated-task output byte-for-byte unchanged. Manually exercised add/list/done/rm with and without --due, invalid dates (wrong shape, impossible date like 2026-02-30, non-leap-year 2026-02-29), overdue filtering, done-exclusion, and the due-today boundary (correctly not overdue) — all behave as the spec describes. presubmit (compileall + full unittest suite, 21 tests) passes. No scope creep: no editing/clearing due dates, no sorting, no timezone config — all correctly left out per the spec's explicit non-goals. Follows AGENTS.md: stdlib only, Python 3.9-compatible syntax, task ids untouched, backward-compatible file format via .get(), stderr/exit-1 error convention preserved, and new behavior is covered by new regression tests in both test_store.py and test_cli.py.

Invariants: 7/7 satisfied

---
**factory-merge** · 2026-10-09 00:42 UTC

Branch conflicts with main. Sent back to the implementer.
