---
title: its broken
author: anon42
state: open
labels: triaged, bug, area:cli, repro:not-applicable, needs-info
---
doesnt work on my machine sometimes. pls fix asap

---
**factory-triage** · 2026-10-09 00:17 UTC

Type: bug (reported as such), but there is nothing here to act on.

The report is just "doesnt work on my machine sometimes. pls fix asap" — no command run, no expected vs. actual output, no error message/traceback, no OS/Python version, and no indication of whether this is reproducible every time or intermittent in a specific way. I tried the obvious smoke test with an isolated `--db` under `$TMPDIR`:

    python3 -m tasklite --db /tmp/.../scratch.json add "a"
    python3 -m tasklite --db /tmp/.../scratch.json list

and it worked fine, as expected — there's no concrete scenario in the report to even attempt to reproduce the claimed failure. `tasklite/cli.py` and `tasklite/store.py` (`tasklite/store.py:1-44`) are small enough that I could point at specific lines if given a failing command, but "sometimes" without any trigger gives nothing to go on.

Duplicate check: not a duplicate of `issues/GH1.md` (confirmed `done`/index bug), `issues/GH2.md` (due-dates feature), or `issues/GH4.md` (sync feature) — those are all concrete and unrelated; this report could coincidentally be about any of them (e.g. it's plausible the reporter hit the same `done`-after-`rm` bug as GH1), but there's no way to tell from the text given.

Recommend `needs-info`. Ask the reporter for:
- The exact command(s) run, in order (ideally the full transcript, like GH1's report had).
- What they expected vs. what actually happened (exact output or error text).
- Whether it fails every time with those commands or only intermittently, and if intermittent, how often / under what conditions.
- OS, Python version, and the `tasklite` version/commit.
- The path/contents of the task db file if possible (redacted if needed), since `Store.__init__` (tasklite/store.py:16-20) loads `next_id`/`tasks` straight from JSON with no validation — a malformed or hand-edited file could raise an unhandled exception, but we can't confirm that without seeing it.

Recommended readiness: `needs-info`
