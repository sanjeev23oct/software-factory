# Engineering guide

This repository holds `tasklite`, a small task tracker, and the software
factory that maintains it. Humans and agents follow the same rules.

## Layout

- `tasklite/` is the product. `store.py` owns persistence, `cli.py` owns
  argument parsing and output. Keep that split.
- `tests/` holds the unit tests, one file per module.
- `specs/GH<n>/` holds `product.md` and `tech.md` for feature issue `GH<n>`.
- `issues/` is the issue tracker. Only the factory writes there.
- `factory/` is the orchestrator. Product work never touches it.

## Rules

- Standard library only. No third-party dependencies.
- Python 3.9 compatible.
- Task ids are permanent. An id is never reused or renumbered.
- The task file format is user data. A change to it must still load files
  written by earlier versions.
- User-facing errors go to stderr as `error: <message>` with exit code 1.
- Every bug fix lands with a regression test that fails without the fix.
- Every new behavior lands with tests for it.
- Run `./script/presubmit` before you call the work done. It must pass.
- Do not commit. The factory commits for you.
