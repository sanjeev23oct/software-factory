# bugfix factory

Bug reports from Jira. No spec: reproduce with a failing test, fix, verify, review, then one human approval.

The fast lane. Nothing waits for a person until a reviewed, verified fix exists. The failing test written in the first stage is the proof the bug was real and is gone.

| # | Stage | Done by | Notes |
| --- | --- | --- | --- |
| 1 | read-issue | Script | `read-issue` |
| 2 | reproduce | Agent | `reproduce-bug` |
| 3 | fix | Agent | `fix-bug` |
| 4 | verify | Script | `verify`, on failure back to `fix` |
| 5 | review | Agent | `review-change` |
| 6 | check-review | Script | `check-review`, on failure back to `fix` |
| 7 | approve-fix | **Human** |  |
| 8 | merge-request | Script | `open-merge-request`, optional, off |

Starts from: Jira issues.

## Use it

    python3 factory/flow.py init my-project --sample bugfix --repo /path/to/your/repo

Then edit `targets/my-project/factory.json` (the source), `AGENTS.md` (your rules) and `presubmit` (your checks).
