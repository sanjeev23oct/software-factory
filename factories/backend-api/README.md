# backend-api factory

Backend and database work from GitHub issues. Design is required and approved separately, because API and schema changes are expensive to undo.

Two human decisions: what to build, then how. The design must spell out request and response shapes and every schema change before any code is written.

| # | Stage | Done by | Notes |
| --- | --- | --- | --- |
| 1 | read-issue | Script | `read-issue` |
| 2 | requirements | Agent | `write-requirements` |
| 3 | approve-requirements | **Human** |  |
| 4 | design | Agent | `write-design` |
| 5 | approve-design | **Human** |  |
| 6 | tasks | Agent | `write-tasks` |
| 7 | lint-tasks | Script | `lint-tasks`, on failure back to `tasks` |
| 8 | build | Agent | `build-tasks` |
| 9 | check-evidence | Script | `check-evidence`, on failure back to `build` |
| 10 | verify | Script | `verify`, on failure back to `build` |
| 11 | merge-request | Script | `open-merge-request`, optional, off |

Starts from: GitHub issues.

## Use it

    python3 factory/flow.py init my-project --sample backend-api --repo /path/to/your/repo

Then edit `targets/my-project/factory.json` (the source), `AGENTS.md` (your rules) and `presubmit` (your checks).
