# ui-app factory

UI work from GitLab issues. A visual spec pins every screen and state; a human looks at the result before it goes further.

Scripts can check that a screen has the right text and test ids, and that it
typechecks. When the issue has a screenshot attached, they also check that the
screen looks like it: `visual-verify` measures every region of the built screen
against the reference (see [docs/visual-verification/](../../docs/visual-verification/)),
a separate checker judges it by eye, and the person at the screens gate sees
reference, build and difference side by side. Approving saves the screens as
baselines that later changes are checked against.

| # | Stage | Done by | Notes |
| --- | --- | --- | --- |
| 1 | read-issue | Script | `read-issue`; saves attached screenshots to `reference/` |
| 2 | requirements | Agent | `write-requirements` |
| 3 | approve-requirements | **Human** |  |
| 4 | visual-spec | Agent | `write-visual-spec`, optional; writes the region contract for each screenshot |
| 5 | tasks | Agent | `write-tasks`; the page section gets a visual gate |
| 6 | lint-tasks | Script | `lint-tasks`, on failure back to `tasks` |
| 7 | build | Agent | `build-tasks`, checked by `check-tasks` and `check-visual` |
| 8 | check-evidence | Script | `check-evidence`, on failure back to `build` |
| 9 | verify | Script | `verify`, on failure back to `build` |
| 10 | visual-verify | Script | `visual-verify`, on failure back to `build`; commits its evidence |
| 11 | approve-screens | **Human** | shows reference vs built; approving saves baselines |
| 12 | pull-request | Script | `open-pull-request`, optional |
| 13 | merge-request | Script | `open-merge-request`, optional, off |

Starts from: GitLab issues.

## Use it

    python3 factory/flow.py init my-project --sample ui-app --repo /path/to/your/repo

Then edit `targets/my-project/factory.json` (the source), `AGENTS.md` (your rules) and `presubmit` (your checks).
