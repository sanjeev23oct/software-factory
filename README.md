# software-factory

A proof of concept of the workflow Warp uses to run
[warpdotdev/warp](https://github.com/warpdotdev/warp), rebuilt on Claude Code.

In Warp's repository, agents triage issues, write specs, implement changes and
give the first review of every pull request. Humans decide what is ready to be
worked on and what is allowed to merge. This repository does the same thing on
a small real product, `tasklite`, with headless Claude Code (`claude -p`) in
place of Warp's Oz agents and a local issue tracker in place of GitHub.

## The pipeline

    filed ──▶ triage ──▶ [human: readiness label] ──▶ spec ──▶ [human: approve spec]
                                   │                                    │
                                   └── bugs skip the spec ──────────────┤
                                                                        ▼
              merged ◀── [human: merge] ◀── agent review ◀──────── implement
                                                 │                      ▲
                                                 └── changes requested ─┘  (3 rounds, then a human)

| Stage | Who | What happens |
| --- | --- | --- |
| Triage | `triager` agent | Classifies the issue, reproduces bugs, checks for duplicates, recommends a readiness label. |
| Readiness | Human | Applies `ready-to-spec` (features) or `ready-to-implement` (bugs, or features with approved specs). |
| Spec | `spec-writer` agent | Writes `specs/GH<n>/product.md` (numbered behavior invariants) and `tech.md`. |
| Implement | `implementer` agent | Writes code and tests on the issue's branch, in its own git worktree. |
| Review | `reviewer` agent | Checks the diff against the issue and every spec invariant. Approves or requests changes. |
| Merge | Human | Final review, then `merge`. |

## What the factory enforces

The agents are prompted, but the rules below are code in
[factory/factory.py](factory/factory.py) and hold whatever an agent says.

- Agents never apply readiness labels and never merge.
- A feature cannot become `ready-to-implement` until both spec files exist.
- `needs-info`, `duplicate`, `reserved-internal` and `needs-human` stop all agent work.
- The factory runs `./script/presubmit` itself before every review. A failing
  branch goes back to the implementer without a review.
- A review with any blocking finding or any unmet invariant is not an approval,
  whatever verdict the reviewer gave.
- After three rejected review rounds the issue is escalated to a human.
- `merge` runs presubmit on the merged result and backs the merge out if it fails.
- Agents never commit. The factory commits what they leave in the worktree.

## Run it

Requires `claude` (Claude Code) on your path, Python 3.9+, and git.

    python3 factory/factory.py status            # the board
    python3 factory/factory.py run               # agents advance every issue as far as they may
    python3 factory/factory.py label GH2 ready-to-spec
    python3 factory/factory.py merge GH1
    python3 factory/factory.py new "title" --body "what is wrong"

`run` stops at each human gate and says what it is waiting for. Each issue's
history is in `issues/GH<n>.md`. Its work in progress is in
`.factory/worktrees/GH<n>/`, and the raw result and cost of every agent run is
in `.factory/runs/GH<n>/`.

`FACTORY_MODEL` picks the model. `FACTORY_MAX_BUDGET_USD` caps one agent run
(default 3).

## Where things live

- [factory/factory.py](factory/factory.py): the orchestrator and the gates.
- [.claude/agents/](.claude/agents/): the four agents and the tools each may use.
- [.claude/skills/](.claude/skills/): how to write a product spec and a tech spec.
- [AGENTS.md](AGENTS.md): the engineering rules agents and humans follow.
- [issues/](issues/): the issue tracker. Labels are the state machine.
- [tasklite/](tasklite/), [tests/](tests/): the product.

## How this maps to Warp

| Warp | Here |
| --- | --- |
| GitHub issues and labels | `issues/GH<n>.md` |
| Oz cloud agents | `claude -p --agent <name>` |
| `ready-to-spec`, `ready-to-implement` | The same labels |
| `specs/GH<n>/product.md`, `tech.md` | The same paths |
| `/write-product-spec`, `/write-tech-spec` skills | `.claude/skills/` |
| `warp:reserved-internal` | `reserved-internal` |
| Oz first review, then a Warp engineer | `reviewer` agent, then `merge` |
| `/warp-agent-review`, three per PR | Three review rounds, then `needs-human` |
| `./script/presubmit` | `./script/presubmit` |
| Pull request | Branch `factory/GH<n>` |

## Not built

- GitHub. Issues, labels and pull requests are local files and branches.
- Parallelism. `run` works one issue at a time.
- A sandbox. The implementer may run `python3` in its worktree.
