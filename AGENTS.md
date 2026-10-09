# Engineering guide

This repository holds `tasklite`, a small task tracker, and the software
factory that maintains it. Humans and agents follow the same rules.

## Layout

- `tasklite/` is the product. `store.py` owns persistence, `cli.py` owns
  argument parsing and output. Keep that split.
- `tests/` holds the unit tests, one file per module.
- `specs/GH<n>/` holds `product.md` and `tech.md` for feature issue `GH<n>`.
- `issues/` is the issue tracker. Only `factory/factory.py` writes there.
- `factory/` is the orchestrator. Product work never touches it.
- `.agents/skills/` holds the skills the factory's agents follow.
  `.claude/skills` links to it.
- `.github/issue-triage/config.json` is the label taxonomy.

## Rules

- Standard library only. No third-party dependencies.
- Python 3.9 compatible.
- Task ids are permanent. An id is never reused or renumbered.
- The task file format is user data. A change to it must still load files
  written by earlier versions.
- User-facing errors go to stderr as `error: <message>` with exit code 1.
- Every bug fix lands with a regression test that fails without the fix.
- Every new behavior lands with tests for it.
- Specs describe what ships. A change in behavior updates `specs/GH<n>/` on
  the same branch.
- Comments explain why, never what.
- Run `./script/presubmit` before you call the work done. It must pass.

## The factory

Issues move through triage, spec, implementation, and review. To work on an
issue through the factory, use the `factory` skill. Readiness labels
(`ready-to-spec`, `ready-to-implement`, `plan-approved`) and merges are
maintainer decisions.
