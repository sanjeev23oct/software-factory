---
title: Traceback when the task file is empty
author: dana
state: open
labels: agent:bug, area:storage, agent:priority-high, repro:high, triaged, ready-to-implement, agent-approved
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

---
**maintainer** · 2026-10-09 02:19 UTC

Applied label `ready-to-implement`.

---
**factory-implementation** · 2026-10-09 02:21 UTC

# GH5: Traceback when the task file is empty

## Change

- `tasklite/store.py`: added `InvalidTaskFile` exception. `Store.__init__`
  now catches `json.JSONDecodeError` (malformed/empty file) and
  `KeyError`/`TypeError` (valid JSON missing the `next_id`/`tasks` shape,
  e.g. `{}`) and raises `InvalidTaskFile(path)` instead of letting the
  original exception propagate.
- `tasklite/cli.py`: moved `store = Store(args.db)` inside the existing
  `try` block (it was previously constructed before the block, so any
  error it raised could never reach the `error: ...` / exit-1 path) and
  added an `except InvalidTaskFile` branch that prints
  `error: <path> is not a valid task file` to stderr and returns exit
  code 1, matching the existing `TaskNotFound` handling.

## Root cause

`Store.__init__` called `json.load(f)` with no error handling, and the
`Store` construction in `cli.py` sat outside the command dispatch's
`try`/`except`, so a 0-byte (or otherwise malformed) task file produced an
uncaught `JSONDecodeError` traceback instead of a clean error.

## Validation

- Added regression tests:
  - `tests/test_store.py::test_empty_file_raises_invalid_task_file` —
    confirmed this fails with the original code (import error on the new
    `InvalidTaskFile` symbol, then a `JSONDecodeError` once the symbol
    exists) before the fix, and passes after.
  - `tests/test_store.py::test_file_missing_required_keys_raises_invalid_task_file`
    — covers valid-JSON-but-wrong-shape files (e.g. `{}`).
  - `tests/test_cli.py::test_empty_db_file_reports_clean_error` — asserts
    the CLI exits 1 with `error: <path> is not a valid task file` on
    stderr and nothing on stdout.
- Ran `./script/presubmit`: passes (12 tests, OK).
- Manually reproduced the original report: `python3 -m tasklite --db
  <empty-file> list` now prints `error: <path> is not a valid task file`
  and exits 1, no traceback.

## Notes

- No `specs/GH5/` exists for this issue; it's a bug fix restoring expected
  error-handling behavior, not a new feature, so no spec was added.
- Scope kept to the two files the triage comment pointed at
  (`tasklite/store.py`, `tasklite/cli.py`) plus their tests.

Branch: `factory/GH5`

---
**factory-review** · 2026-10-09 02:23 UTC

**Review round 1: approve**

## Overview
Fixes the traceback reported in GH5: a 0-byte (or otherwise malformed/wrong-shape) task file now raises a new `InvalidTaskFile` instead of letting `json.JSONDecodeError`/`KeyError`/`TypeError` escape, and `cli.py` catches it alongside `TaskNotFound` to print `error: <path> is not a valid task file` and exit 1.

Verified the root cause fix is complete, not partial: `Store(args.db)` was moved inside the dispatch `try` block (it previously sat outside it, so even a clean exception from `Store` couldn't have reached the error path), and the catch in `Store.__init__` covers decode failure, missing keys, and wrong-shape JSON (list/str/int/null all raise `TypeError` on the subscript, so they're caught too). Confirmed by reasoning from the diff that both new regression tests fail against the pre-fix code (import error on the new `InvalidTaskFile` symbol, since it doesn't exist pre-fix) and pass after. Ran `./script/presubmit`: 12 tests, OK. Store/CLI split is preserved, no third-party imports, error goes to stderr with exit 1 per convention, and test comments explain why (reference GH5) rather than restating the code. Scope is tight to the two files the triage pinpointed plus their tests; no spec was needed, consistent with GH1's precedent of not requiring `specs/` for a bug fix that restores expected error handling rather than adding new behavior.

## Concerns
- None blocking.

## Suggestions
- `tasklite/store.py:27` — minor: suppress the chained traceback when re-raising, see inline comment.

## Verdict
Found: 0 critical, 0 important, 1 suggestion

**Approve**

`tasklite/store.py:27` 💡 [SUGGESTION] This re-raise implicitly chains the original `JSONDecodeError`/`KeyError`/`TypeError` as the cause. It's harmless today since the error is only ever stringified, but if anything later logs or prints this exception's traceback, the internal cause will leak through. Suppress it explicitly:

```suggestion
                    raise InvalidTaskFile(path) from None
```
