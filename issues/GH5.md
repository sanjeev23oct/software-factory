---
title: Traceback when the task file is empty
author: dana
state: open
labels: agent:bug, area:storage, agent:priority-high, repro:high, triaged
---
My disk filled up and tasks.json ended up as a 0 byte file. Now every command dumps a Python traceback:

    $ python3 -m tasklite list
    Traceback (most recent call last):
      ...
    json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

I get that the file is broken, but I would expect a normal error message telling me which file is bad, not a stack trace.

---
**factory-triage** · 2026-10-09 02:18 UTC

Confirmed. Reproduced the exact traceback: writing a 0-byte file and running `python3 -m tasklite --db <file> list` raises `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`.

Root cause: `Store.__init__` (`tasklite/store.py:16-20`) calls `json.load(f)` with no error handling. A 0-byte file isn't valid JSON, so `json.load` raises `JSONDecodeError`. Making it worse, `Store(args.db)` is constructed in `cli.py:35` *outside* the `try`/`except` block that wraps command dispatch (`cli.py:37-55`), so even a caught/translated error inside `Store` wouldn't currently reach the `error: <message>` / exit-1 path without also moving or widening that `try`.

Fix should catch the decode failure (and likely a missing/invalid `next_id`/`tasks` key) in or around `Store.__init__`, and surface it as `error: <path> is not a valid task file` (or similar) on stderr with exit code 1, consistent with the `TaskNotFound` handling already in `cli.py`. A regression test should cover constructing `Store` against a 0-byte file and asserting the clean error instead of a traceback.

Not a duplicate: `GH3` ("its broken") is too vague to match on title or error text — it speculates generically about unhandled exceptions in `Store.__init__` but doesn't report this specific symptom. No other open issue describes this crash.

Recommend `ready-to-implement`: bug reproduced, root cause pinpointed, fix is narrow and localized to `tasklite/store.py` (and possibly where errors are caught in `tasklite/cli.py`).

Readiness recommendation for the maintainer: `ready-to-implement`
