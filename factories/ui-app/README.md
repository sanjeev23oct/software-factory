# ui-app factory

UI work from GitLab issues. A visual spec pins every screen and state; a human looks at the result before it goes further.

Scripts can check that a screen has the right text and test ids, and that it typechecks. They cannot tell whether it looks right. So this factory ends with a person looking at it.

| # | Stage | Done by | Notes |
| --- | --- | --- | --- |
| 1 | read-issue | Script | `read-issue` |
| 2 | requirements | Agent | `write-requirements` |
| 3 | approve-requirements | **Human** |  |
| 4 | visual-spec | Agent | `write-visual-spec`, optional |
| 5 | tasks | Agent | `write-tasks` |
| 6 | lint-tasks | Script | `lint-tasks`, on failure back to `tasks` |
| 7 | build | Agent | `build-tasks` |
| 8 | check-evidence | Script | `check-evidence`, on failure back to `build` |
| 9 | verify | Script | `verify`, on failure back to `build` |
| 10 | approve-screens | **Human** |  |
| 11 | merge-request | Script | `open-merge-request`, optional, off |

Starts from: GitLab issues.

## Use it

    python3 factory/flow.py init my-project --sample ui-app --repo /path/to/your/repo

Then edit `targets/my-project/factory.json` (the source), `AGENTS.md` (your rules) and `presubmit` (your checks).
