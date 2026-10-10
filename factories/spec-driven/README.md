# spec-driven factory

Requirement to requirements, one approval, optional design, tasks with a skill each, maker-checker build with evidence.

The general-purpose factory. One human decision, on the requirements. Everything after that is checked by scripts. Use it for full-stack feature work, and as the base for your own.

| # | Stage | Done by | Notes |
| --- | --- | --- | --- |
| 1 | read-issue | Script | `read-issue` |
| 2 | requirements | Agent | `write-requirements` |
| 3 | approve-requirements | **Human** |  |
| 4 | design | Agent | `write-design`, optional |
| 5 | tasks | Agent | `write-tasks` |
| 6 | lint-tasks | Script | `lint-tasks`, on failure back to `tasks` |
| 7 | build | Agent | `build-tasks` |
| 8 | check-evidence | Script | `check-evidence`, on failure back to `build` |
| 9 | verify | Script | `verify`, on failure back to `build` |
| 10 | merge-request | Script | `open-merge-request`, optional, off |

Starts from: a requirement in a file.

## Use it

    python3 factory/flow.py init my-project --sample spec-driven --repo /path/to/your/repo

Then edit `targets/my-project/factory.json` (the source), `AGENTS.md` (your rules) and `presubmit` (your checks).
