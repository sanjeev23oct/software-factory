---
title: Due dates for tasks
author: marco
state: open
labels: triaged, feature, area:cli
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
