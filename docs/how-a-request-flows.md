# How a request flows

One request, from the issue to the merge request, on a GitLab runner. The names
are examples: a project `shop` whose pipeline lives in `targets/shop/` of the
factory project, and issue #42.

Each **pass** is one run of the factory job. It starts in a fresh container,
clones what it needs, moves every request as far as it can without a person,
saves progress, and exits. Nothing stays on the runner between passes.

```
 project repo (shop)                factory project                          engine repo
 ───────────────────                ────────────────────────────────         ───────────────
 issue filed / reply  ──webhook──►  schedule (*/10) or trigger
                                      │
                                      ▼
                                    factory job, in the runner image
                                      │ clone ────────────────────────────►  flow.py and the checks
                                      │ read targets/shop/ and factory-state
                                      │ clone the project ◄── main + factory/* branches
                                      ▼
                                    flow.py: one pass
                                      • new issues and replies (GitLab API)
                                      • per request, its next stages:
                                          agents: claude -p in a worktree of the project,
                                                  with its CLAUDE.md and .claude/skills
                                          scripts: plan lint, evidence, presubmit, visual checks
                                      • comments on the issue, pushes factory/GL<n>,
                                        opens the merge request at the end
                                      ▼
                                    progress saved to factory-state; container deleted
```

## 0. Someone files an issue

In the project, with the Feature template: *"Add a filter by department on the
staff list."* The template's last line adds the `factory` label. The project's
webhook starts a pipeline in the factory project within seconds; without one,
the 10-minute schedule picks it up.

## Every pass starts the same way

| Step | What happens | Where, in the job's container |
|---|---|---|
| 1 | The runner starts the factory job in the runner image | the job's checkout of the factory project |
| 2 | The job clones the engine at `FACTORY_REF` | `/opt/software-factory` |
| 3 | Progress is pulled from the `factory-state` branch | `.factory-work/state/` |
| 4 | `flow.py` reads `targets/shop/target.json`, sees `remote`, and clones the project: `main` and every `factory/*` branch, signing in with `FACTORY_GITLAB_TOKEN` | `.factory-work/repos/shop/` |
| 5 | Each request gets a git worktree on its own branch, `factory/GL<n>`: agents work there, never on `main`, and two requests never share files | `.factory-work/state/shop/worktrees/GL<n>/` |

## Pass 1: from the issue to "approve the requirements" (a few minutes)

| Stage | Who | What happens |
|---|---|---|
| poll | script | Finds #42 labelled `factory` and opens request GL42 |
| read-issue | script | Saves the issue text, and an attached screenshot as the visual reference |
| requirements | agent | One `claude -p` session in the worktree reads the pipeline's `AGENTS.md`, the project's `CLAUDE.md` and its code, and writes `specs/42-…/requirements.md`: user stories, acceptance criteria, open questions. The factory checks it changed only what it may, then commits |
| visual-spec | agent | Only with a screenshot: the screen's measurable contract |
| **approve-requirements** | **person** | The factory pushes `factory/GL42`, comments a progress table and *"The factory is waiting for you"* with a link to the requirements, saves progress, and the job ends |

**The person** replies `approve`, which starts the next pass. Or they reply with
answers or changes: the next pass hands the reply to the requirements agent,
which revises the document, and the gate opens again with a new link.

## Pass 2: build and check (the long one, 15–40 minutes)

| Stage | Who | What happens |
|---|---|---|
| gates | script | Reads the `approve` and moves GL42 on |
| tasks | agent | `tasks.md`: sections of tasks, each naming the skill that builds it (from the pipeline or the project's `.claude/skills`, e.g. `/build-api-controller`), and runnable checks in `loop/*-checker.md` |
| lint-tasks | script | Every task names a skill that exists and fits its files; if not, the plan goes back to the agent |
| build | maker, then checker | Per section: a **maker** session builds it by following the named skills and commits. A **checker**, a separate session that never saw the maker, runs the section's checks and tests, writes `evidence/<n>-gate.md`, and ticks the section only if everything passed. A failure goes back to the maker with the findings, up to three tries |
| check-evidence | script | Re-runs the commands the checkers recorded: the factory never takes an agent's word for a result |
| verify | script | `targets/shop/presubmit`: the project's build and tests. A failure goes back to build |
| security | script | **Mandatory.** What the change adds, compared with `main`: secrets (gitleaks), risky code (semgrep), and new high or critical vulnerable packages (`dotnet list package --vulnerable`, `pnpm audit`). Findings go back to the maker; a check that cannot run stops the request for a person. The report is committed as `evidence/security.md` |
| visual-verify | script | With a reference screenshot: the built screen measured against it in Chrome |
| ai-review | agent | A reviewer that did not write the change reads the whole diff against the requirements: does it do what was asked, AI slop (dead code, needless abstraction, invented APIs, silent fallbacks), security, the repository's conventions, tests. Writes `review.md` with a verdict |
| check-review | script | Passes only on `Verdict: APPROVE`; blocking findings go back to the maker, and the review runs again |
| preview | script | Posts the **Try it** link, when a preview deployment is set up |
| **approve-screens** | **person** | Pushes the branch, comments *"waiting for you"* with the evidence and screenshots, saves progress, and the job ends |

The issue's progress comment shows each step as it happens.

**The person** tries it and replies `approve`. Or they reply with what is wrong:
the next pass hands the reply to the build's maker, which reworks the change; the
scripts check it again, and the gate reopens with a new **Try it** link.

## Pass 3: hand-over (a minute)

| Stage | Who | What happens |
|---|---|---|
| gates | script | Reads the second `approve` |
| merge-request | script | Opens a merge request from `factory/GL42` into `main` with the code, the tests, the requirements, the plan and all the evidence, and links it on the issue |

The request is done. **A person reviews and merges** the merge request like any
other: the project's own CI runs, and its normal deployment takes it from there.
The factory never merges.

## Cost and limits

**Models by kind of work.** Planning (requirements, design, plan) uses a stronger model; building and
checking (makers, checkers, the reviewer), which are most of the sessions, a cheaper one. Defaults:
`plan` opus, `build` sonnet, `check` sonnet. A pipeline changes them in `factory.json`,
`"models": {"plan": "opus", "build": "sonnet", "check": "haiku"}`, and one stage with `"model"`.
`FACTORY_MODEL` forces one model for every run.

**Checked sections are pushed as they pass,** so the branch on GitLab shows the work as it is built,
and a pass that dies part-way loses no checked section.

A typical request is 10 to 12 agent sessions: requirements, plan, and a maker
and a checker per section, plus any retries. A session stops at
`FACTORY_MAX_BUDGET_USD` (default 3); a stage that fails three times stops and
asks a person; and `limits.daily_usd` in `factory.json` pauses agent work for
the day once that much has been spent.
