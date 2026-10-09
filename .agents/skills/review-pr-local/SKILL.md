---
name: review-pr-local
specializes: review-pr
description: Repo-specific review guidance for tasklite. Only the categories the core review-pr skill marks as overridable are specialized here.
---

# Repo-specific review guidance for `tasklite`

## Recurring review patterns

- Ids are permanent. Flag any code that treats a task id as a list position,
  renumbers ids, or reuses one.
- The task file is user data. A change to what is stored must still load a
  file written by an earlier version. Missing that is `🚨 [CRITICAL]`.
- `store.py` owns persistence and `cli.py` owns parsing and output. Flag
  printing in the store or file access in the CLI.
- Any third-party import is `⚠️ [IMPORTANT]`. Standard library only.
- User-facing errors go to stderr as `error: <message>` with exit code 1. A
  traceback reaching the user is a bug.

## Testing

- A bug fix without a regression test that fails before the fix is
  `⚠️ [IMPORTANT]`. Check out the pre-fix file or reason from the diff to
  confirm the test would have failed.
- New behavior needs a test at the layer that owns it: store behavior in
  `tests/test_store.py`, command behavior in `tests/test_cli.py`.
- Tests that depend on today's date must inject the date, not read the
  clock.

## Comments

- Comments explain why, not what. Flag a comment that restates the code or
  that describes the edit ("now uses", "changed to") instead of the current
  state.
- A regression test may name the issue it guards.
