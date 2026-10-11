# software-factory

A working copy of the software factory Warp runs on
[warpdotdev/warp](https://github.com/warpdotdev/warp), rebuilt to run on
Claude Code.

In Warp's repository, agents triage issues, write specs, implement changes,
and give the first review of every pull request. Maintainers decide what is
ready to be worked on and what may merge. Warp open-sourced that system as
[warpdotdev/oz-for-oss](https://github.com/warpdotdev/oz-for-oss), with its
shared skills in
[warpdotdev/common-skills](https://github.com/warpdotdev/common-skills).

This repository applies the same contracts to a small real product,
`tasklite`. Claude Code agents stand in for Warp's Oz agents, and a local
issue tracker stands in for GitHub.

## See it run: Idea to Value

[docs/demo/](docs/demo/) holds a recording of the factory being set up and
used for real. [factory-demo.mp4](docs/demo/factory-demo.mp4) is a
seven-minute video in 15 numbered steps: set the factory up, define a route
for a repository, then take one idea from an issue to a pull request, with a
person approving at two gates. [index.html](docs/demo/index.html) is the same
walkthrough as a page, with the commands for each step.

It ran on [factory-demo-ui](https://github.com/sanjeev23oct/factory-demo-ui)
and [factory-demo-api](https://github.com/sanjeev23oct/factory-demo-api): one
factory, two repositories, five routes.

## The pipeline

    filed ─▶ triage ─▶ [maintainer: ready-to-spec] ─▶ spec ─▶ spec review ─▶ [maintainer: plan-approved]
                 │                                      ▲          │                       │
                 │                                      └─ reject ─┘                       │
                 └─▶ [maintainer: ready-to-implement] ─────────────────────────────────────┤
                                                                                           ▼
                     merged ◀─ [maintainer: merge] ◀─ review ◀─ presubmit ◀─────────── implement
                                                         │                                 ▲
                                                         └──────────── reject ─────────────┘

| Stage | Agent | Skill | Writes |
| --- | --- | --- | --- |
| Triage | `triage` | `triage-issue`, `dedupe-issue` | `triage_result.json` |
| Spec | `spec` | `write-product-spec`, `write-tech-spec` | `specs/GH<n>/product.md`, `tech.md`, `pr-metadata.json` |
| Spec review | `review` | `review-spec` | `review.json` |
| Implement | `implementation` | `implement-issue` | code, tests, `implementation_summary.md`, `pr-metadata.json` |
| Review | `review` | `review-pr`, `check-impl-against-spec` | `review.json` |

A review is rejected at most three times before the issue is escalated to a
maintainer with `needs-human`.

## Run it from Claude Code

Open this folder in Claude Code, in the terminal or in the VS Code extension,
and ask:

    /factory                      show the board and advance every issue
    /factory GH6                  advance one issue
    /factory label GH6 ready-to-spec
    /factory merge GH6

The session acts as foreman. It asks `factory.py next` for a task, starts the
subagent the task names, and runs `factory.py apply` on what the subagent
wrote. It stops at every maintainer gate and waits for you.

## Run it headless

    python3 factory/factory.py run            # every issue, until each needs a maintainer
    python3 factory/factory.py run GH6

This is the same loop with `claude -p` in place of subagents. `FACTORY_MODEL`
picks the model. `FACTORY_MAX_BUDGET_USD` caps one agent run (default 3).

## Other repositories, and defining your own factory

The factory can work on a repository elsewhere on disk. Each one is a folder
under `targets/` holding its guidance, labels, presubmit and skills, so
nothing is added to that repository except `factory/*` branches. Target
folders describe private repositories, so they are git-ignored and are not
part of this repository.

    python3 factory/factory.py targets

A target may also define its own factory in `targets/<name>/factory.json`:
the stages a piece of work goes through, in order, and whether each is done
by a script, by an agent following a skill, or by a human. `factory/flow.py`
runs that definition. One such definition, for a .NET and React application, goes:
requirement, `requirements.md`, human approval, optional `design.md`,
`tasks.md`, a script that checks every task names a skill, the repository's
own maker-checker build loop, a script that checks the evidence, and an
optional merge request.

Scripts in `factory/scripts/` do every step that needs no judgment: reading
an issue from GitHub, GitLab or Jira, linting `tasks.md`, re-checking
evidence, and reading a review verdict.

### Sample factories

[factories/](factories/) holds four definitions to start from, with the
skills they use in [factories/skills/](factories/skills/).

| Sample | For | Starts from | Human decisions |
| --- | --- | --- | --- |
| [spec-driven](factories/spec-driven/) | Full-stack features | A file | Requirements |
| [backend-api](factories/backend-api/) | API and database work | GitHub issues | Requirements, then design |
| [ui-app](factories/ui-app/) | UI work | GitLab issues | Requirements, then the finished screens |
| [bugfix](factories/bugfix/) | Bug reports | Jira issues | The reviewed fix |

Create your own from one:

    python3 factory/flow.py init shop --sample backend-api --repo ~/code/shop
    python3 factory/flow.py --target shop show
    python3 factory/flow.py --target shop validate

Then edit `targets/shop/factory.json`, `AGENTS.md` and `presubmit`.

### Editing a factory without touching files

    python3 factory/editor.py

opens a local page with two tabs. **Route** shows the stops and gates as a
list you reorder, switch on or off, and add to, with a drawing of the route
that updates as you edit. **Review rules** sets how strict each process check
is, lets you add your own rules by filling in a sentence, and can try them on
a real merge request before you save. It serves on 127.0.0.1 only.
[docs/index.html](docs/index.html) explains the concept and walks through
creating a factory. `python3 factory/scripts/build_docs.py` regenerates it
from the samples.

Jira reading is written but has not been run against a real Jira. Nothing
writes back to GitHub, GitLab or Jira.

## Maintainer commands

    python3 factory/factory.py status
    python3 factory/factory.py new "title" --body "what is wrong"
    python3 factory/factory.py comment GH3 "the answer to your question"
    python3 factory/factory.py label GH6 ready-to-spec
    python3 factory/factory.py label GH6 plan-approved
    python3 factory/factory.py label GH5 ready-to-implement
    python3 factory/factory.py merge GH5

An issue's history is in `issues/GH<n>.md`. Its branch is checked out at
`.factory/worktrees/GH<n>/`. Every result an agent produced is kept in
`.factory/runs/GH<n>/`.

## What the factory enforces

Agents are guided by skills. The rules below are code in
[factory/factory.py](factory/factory.py) and hold whatever an agent does.

- Agents never change an issue, commit, or merge. They write result files.
  The factory validates them and applies them.
- `ready-to-spec`, `ready-to-implement` and `plan-approved` can only be
  applied by the `label` command. A triage result that contains one is
  rejected.
- Triage may only apply labels that
  [.github/issue-triage/config.json](.github/issue-triage/config.json) gives
  to triage, with exactly one primary type.
- An issue is marked duplicate only when two or more existing issues match.
- Each stage may only write where it is meant to. Triage and review may
  change nothing. Spec may change only `specs/GH<n>/`. Implementation may not
  touch the tracker, the factory, the skills, or the presubmit script.
- Every inline review comment must point at a real line of the annotated
  diff and carry a severity label. An approval that carries a critical or
  important comment is rejected.
- The factory runs `./script/presubmit` itself before every review. A failing
  branch goes back to implementation without a review.
- A branch that conflicts with main, or fails presubmit once merged, goes
  back to implementation and is reviewed again.
- `needs-info`, `duplicate`, `reserved-internal` and `needs-human` stop all
  agent work on an issue.
- Agents read skills from main, not from their own branch.
- Issue text reaches agents as a file marked untrusted, never as part of the
  prompt.

## Where things live

- [.agents/skills/](.agents/skills/): the skills. `.claude/skills` links here.
- [.claude/agents/](.claude/agents/): the four role agents and their tools.
- [factory/factory.py](factory/factory.py): task hand-out, validation, gates.
- [.github/issue-triage/config.json](.github/issue-triage/config.json): the
  label taxonomy and who may apply each label.
- [AGENTS.md](AGENTS.md): the engineering rules. `CLAUDE.md` imports it.
- [issues/](issues/): the tracker. [specs/](specs/): approved specs.
- [tasklite/](tasklite/), [tests/](tests/): the product.

## What comes from Warp

| Practice | Source | Here |
| --- | --- | --- |
| Skills hold the intelligence; the rest is wiring | oz-for-oss README | `.agents/skills/` |
| Core skill plus a `-local` companion that may override only named categories | `triage-issue`, `review-pr`, `dedupe-issue` | `triage-issue-local`, `review-pr-local`, `dedupe-issue-local` |
| `.agents/skills` as the home, linked from `.claude/skills` | warp repository layout | The same |
| Agents write `triage_result.json`, `review.json`, `pr-metadata.json`, `implementation_summary.md`; the workflow applies them | oz-for-oss skills | The same file names |
| Readiness labels reserved for maintainers | `triage-issue`, CONTRIBUTING | Enforced in `label` and in triage validation |
| `plan-approved` releases a specced feature | oz-for-oss routing | The same label |
| Label taxonomy in `.github/issue-triage/config.json` | Both repositories | The same path |
| `specs/GH<n>/product.md` and `tech.md` | Both repositories | The same paths |
| Product spec is Summary plus numbered Behavior invariants, no validation section | `write-product-spec` | The same structure |
| Tech spec is Context, Proposed changes, Testing and validation | `write-tech-spec` | The same structure |
| Specs are reviewed by an agent before a maintainer approves | `review-spec` | The spec review stage |
| Specs stay current with the code on the same branch | `implement-specs` | `implement-issue`, `check-impl-against-spec` |
| Annotated diff, severity labels, `APPROVE`/`REJECT` verdict | `review-pr` | The same format |
| Issue content is untrusted data, kept out of the prompt | `implement-issue`, `triage-issue` | `issue_context.md` |
| Duplicates need two matches; duplicates and questions exclude each other | `dedupe-issue`, `triage-issue` | Enforced when triage is applied |
| Write-surface guard on what an agent changed | `update-triage` | Applied to every stage |
| Three agent reviews per pull request | CONTRIBUTING | Three rounds, then `needs-human` |

The skills are written for this repository, following the contracts of
Warp's. They are not copies of Warp's text.

## Not built

- GitHub. Issues, labels, and pull requests are local files and branches.
  Warp's triggers are webhooks on label and comment events.
- The self-improvement loops (`update-triage`, `update-pr-review`,
  `update-dedupe`) that rewrite the `-local` skills from maintainer overrides.
- `verify-pr` and the security review skills.
- Owner inference from a `STAKEHOLDERS` file.
- Parallelism. One issue is worked at a time.
- A sandbox. The implementation agent may run `python3` in its worktree.
