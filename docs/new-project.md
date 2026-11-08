# Bring a project into the factory

This guide takes a repository, new or existing, from "we use Claude Code on it"
to "requests go through the factory": an issue in, requirements you approve, a
maker and a separate checker building it section by section, evidence for every
check, and a merge request out.

It takes about an hour for a repository that already builds and tests from the
command line. Most of that time is writing down rules you already follow.

> **New client on the factory server instead?** If you want an empty app that
> grows one request at a time, on the server that already runs the factory, use
> `sandbox/setup.sh`: one command. See [sandbox/README.md](../sandbox/README.md).
> This guide is for your own codebase, with its own stack.

---

## What you end up with

```
your repository                         the factory (this repository)
───────────────                         ──────────────────────────────────────────
src/, tests/ ...       ◄── branches ──  targets/<name>/
CLAUDE.md              factory/<item>     factory.json   the pipeline: stages, gates, limits
.claude/skills/                           target.json    where the repo is, what agents may run
                                          AGENTS.md      the rules agents read before every task
issues (GitLab,  ──── read by ──────►     presubmit      the checks every change must pass
GitHub or Jira)                           skills/        how each kind of job is done
```

The factory adds nothing to your repository except `factory/<item>` branches,
and the specs and evidence on them. Its pipeline lives in `targets/<name>/`.

---

## Before you start

| You need | Why |
|---|---|
| **A repository that builds and tests from one command** | The factory trusts commands, not claims. If `npm test` or `dotnet test` doesn't run cleanly in a terminal today, fix that first. |
| **Issues somewhere the factory can read** | GitLab, GitHub or Jira, or files on disk for a dry run. |
| **A Claude login** | Your subscription (`claude setup-token`) for your own use, or an Anthropic API key when the factory works for other people. |
| **Somewhere to run it** | Your laptop (Claude Code, or a background job), or a GitLab runner. You can start on the laptop and move later. |
| **Python 3.9+ and git** | The factory is plain Python with no dependencies. |

---

## Step 1. Prepare the repository

### A new repository

Give the factory something to build on. Agents match what they find, so an
empty folder gives them nothing to match.

1. Create the repository with a minimal skeleton in your stack: one page or one
   endpoint, one test, and the test command wired up.
2. Add a `CLAUDE.md` with the stack, the folder layout, and how to run the tests.
   The factory's agents read it (see step 6).
3. Push it, with `main` as the default branch.

### An existing repository

1. Check that the build and the tests run from a clean checkout with one command
   each, with no prompts and no manual setup.
2. Note what agents must never touch: migrations already applied, generated
   code, CI files, secrets. You'll protect them in step 5.
3. Look at what you already have: `CLAUDE.md`, `AGENTS.md`, `.claude/skills/`,
   `.claude/agents/`, linters, coding standards. Step 6 puts all of it to work.

---

## Step 2. Create its pipeline from a sample

Pick the sample closest to the work you want the factory to do:

| Sample | For | Issues from | People decide |
|---|---|---|---|
| [`ui-app`](../factories/ui-app/) | UI work; can check screens against a reference screenshot | GitLab | the requirements, then the finished screens |
| [`backend-api`](../factories/backend-api/) | APIs and databases | GitHub | the requirements, then the design |
| [`spec-driven`](../factories/spec-driven/) | full-stack features | a file | the requirements |
| [`bugfix`](../factories/bugfix/) | bug reports | Jira | the reviewed fix |

From this repository:

```sh
python3 factory/flow.py init shop --sample ui-app --repo ~/code/shop
python3 factory/flow.py --target shop show        # the stages, who does each, and with which skill
```

This writes `targets/shop/`. You can do the same, and every later step, on a
page instead of in files: `python3 factory/editor.py` opens the editor, which
adds a repository, picks a sample, and edits stages, skills and rules.

---

## Step 3. Say where work comes from, and who approves

Edit `targets/shop/factory.json` (the `//` notes are for this guide; JSON has no comments, so leave them out):

```json
"source": {
  "type": "gitlab",                     // gitlab, github, jira or file
  "host": "gitlab.example.com",
  "project": "team/shop",               // github: "repo": "owner/shop"; jira: "project": "SHOP"
  "label": "factory",                   // only issues with this label are picked up
  "approvers": ["you", "your-lead"],    // who may reply "approve" at a gate
  "progress": true,                     // comment each step on the issue
  "write": true                         // allowed to comment and open merge requests
},
"auto": true,                            // picked up by the scheduled pass
"limits": { "max_attempts": 3, "daily_usd": 20 }
```

- **Approvers** are the people whose `approve` counts. Use `["*"]` only for a
  private sandbox: then anyone who can comment on the issue can approve.
- **Limits.** A stage that fails `max_attempts` times stops and asks a person.
  `daily_usd` pauses agent work for the day once that much has been spent. One
  agent run is also capped at `FACTORY_MAX_BUDGET_USD` (default 3).

---

## Step 4. Write the rules agents follow

`targets/shop/AGENTS.md` is the engineering guide. Every agent reads it before
anything else. Start from what you already have:

- **If the repository has a `CLAUDE.md` or `AGENTS.md`, don't copy it.** Agents
  already read it (step 6). Use this file for what the factory needs on top:
  what may never be touched, how a change is verified, and which document wins
  when two disagree.
- Keep it short and concrete: rules a checker can verify beat aspirations.

```markdown
# Engineering guide for factory agents

The repository's CLAUDE.md describes the stack and layout; follow it.

## Rules
- No new dependency without a line in the PR saying why.
- Never edit a migration that has been applied; add a new one.
- Every new behaviour lands with a test.

## Verification
`presubmit` runs the build, the linter and the tests. It cannot see the UI;
the person at the screens gate looks at it through the preview.
```

---

## Step 5. Say how a change is checked, and what agents may run

**`targets/shop/presubmit`** is the gate every change must pass. The factory
runs it itself and never takes an agent's word for it. Call the commands your
CI already runs:

```sh
#!/bin/sh
set -e
npm ci --silent
npm run lint
npm test
```

**`targets/shop/target.json`** says where the repository is, and what agents may do (again, without the `//` note):

```json
{
  "repo": "/Users/you/code/shop",               // on a runner: "remote": "https://gitlab.example.com/team/shop.git"
  "main": "main",
  "protected": [".claude/", ".github/", ".gitlab-ci.yml", "db/migrations/"],
  "allowed_tools": ["Bash(npm:*)", "Bash(node:*)", "Bash(npx:*)"]
}
```

- **`allowed_tools`** are the commands agents may run beyond reading and
  editing files. If the checker can't run your tests, it can't pass anything:
  list every command the presubmit and the checks need (`dotnet`, `pnpm`,
  `pytest`, `go`...).
- **`protected`** paths are never changed by an agent; a stage that touches one
  is rejected. Keep `.claude/` protected so agents can't rewrite your skills.

Then check the whole definition:

```sh
python3 factory/flow.py --target shop validate
```

---

## Step 6. Put your existing Claude Code setup to work

Agents run **inside your repository's checkout, with its project settings**
(`claude -p --setting-sources project`). So most of what your team already
built for Claude Code is used as it is:

| What you already have | How the factory uses it |
|---|---|
| `CLAUDE.md` in the repository | Every agent reads it, as Claude Code always does. Keep the stack and layout there; keep factory-only rules in `targets/<name>/AGENTS.md`. |
| `.claude/skills/` | Available in every agent session. A plan may also name one on a task (`→ run: /your-skill`); the plan checker accepts skills from the repository as well as from the pipeline. |
| `.claude/agents/` | Available as subagents inside each session. |
| `.claude/settings.json`: permissions and hooks | Apply to every agent run. A hook that formats or lints on edit keeps running. |
| Your CI checks, linters, test suites | Call them from `presubmit`. The factory runs it after the build, and the checker runs it per section. |
| Coding standards, architecture notes | Point to them from `AGENTS.md`; agents read what it points at. |
| Review checklists | Make them the checker's skill (below), or the rules a merge request is checked against (`process.json`, the `request-review` sample). |

### Make an existing skill a maker skill

The plan agent chooses a skill for every task, from the pipeline's maker skills:
the ones in `targets/<name>/skills/` whose names start with `build-`. To offer it
one of your own:

1. **Import it into the pipeline** under a `build-` name, either with the
   editor's **Skills → Import** or by copying the folder:
   `cp -r ~/code/shop/.claude/skills/add-endpoint targets/shop/skills/build-endpoint`
2. **Say which files it is for**, in its front matter, so the plan checker can
   tell a task named the right skill:

   ```markdown
   ---
   name: build-endpoint
   description: Add one HTTP endpoint with its handler, validation and route.
   applies_to: src/api/**, src/routes/**
   ---
   ```

3. **Add the factory's maker contract** at the end, the one line that makes it
   safe in a maker/checker loop:

   > You are the maker. Do not tick the task, do not run the section's gate, and
   > do not write evidence. Report what you built and anything the spec left undefined.

### Make an existing review skill the checker

The `build` stage names its checker: `"checker": {"agent": "checker", "skill": "check-tasks"}`.
If your team has a review skill, copy `check-tasks` and add your checklist to it,
then point the stage at the copy. Keep its rules: the checker writes evidence,
ticks a section only when everything passed, and never changes code.

---

## Step 7. Try it on one small issue

1. File a **small, clear** issue with the `factory` label: one change, plain words.
2. Run one pass by hand and watch it:

   ```sh
   python3 factory/flow.py --target shop poll      # pick up new issues
   python3 factory/flow.py --target shop run       # work until a person is needed
   python3 factory/flow.py --target shop status
   ```

3. Read what it wrote on the branch `factory/<item>`: `requirements.md`, then
   approve (reply `approve` on the issue, or `flow.py --target shop approve <item>`).
4. Run it again and read the plan (`tasks.md`), each checker's evidence, and the
   presubmit result. **This first run is where you tune `AGENTS.md`, the skills
   and `allowed_tools`.** Every time you have to step in, change the rule or the
   skill that would have prevented it. That is the factory's meta loop.

---

## Step 8. Choose where it runs

| Where | How | Good for |
|---|---|---|
| **Claude Code, on your laptop** | Open this repository in Claude Code and use `/factory`, or run `flow.py --target shop run` | your own work, watching every step |
| **A background job on your laptop** (macOS) | `python3 factory/scripts/schedule.py install --every 10` | hands-off, while you're logged in |
| **A GitLab runner** | [docs/run-in-gitlab.md](run-in-gitlab.md): a factory project, a schedule, and a webhook for passes as soon as someone files or comments | a team, or anyone without a terminal |

Run it in one place at a time: two factories that don't share progress would
both take the same issues.

---

## Step 9. Add screens to try, and screens to match (UI work)

- **A Try it link** needs a preview server that serves each `factory/<item>`
  branch. The sandbox one ([sandbox/preview/](../sandbox/preview/)) serves
  static sites (HTML, CSS, JavaScript). An app that needs a backend running
  needs its own preview deployment; set `FACTORY_PREVIEW_URL` to its address,
  with `{item}`.
- **Matching a design:** attach a screenshot to the issue. The `ui-app` pipeline
  turns it into a contract you approve, checks the built screen against it, and
  shows reference, built and difference at the screens gate. It needs Chrome on
  whatever runs the factory. See [docs/visual-verification/](visual-verification/).

---

## When something goes wrong

| What you see | What it means | Do this |
|---|---|---|
| `lint-tasks` fails: a task's skill doesn't own its file | The skill named on a task has no `applies_to` that matches the file | Add `applies_to` to the skill, or add a skill for those files |
| The checker fails every section, saying it couldn't run the tests | It isn't allowed to run your test command | Add the command to `allowed_tools` in `target.json` |
| `approve` is ignored | `/approve` with a slash is swallowed by GitLab, or the person isn't in `approvers` | Reply `approve`, without a slash; check `approvers` |
| A stage is **Stopped** after 3 attempts | It failed `max_attempts` times | Read the last findings on the issue, fix the cause, then `flow.py --target shop retry <item>` |
| "changed X, which this stage may not write" or "which is protected" | An agent touched a file outside its stage or a protected path | Usually right to reject. If the stage needs that path, add it to the stage's `writes` |
| Agent work paused for the day | `limits.daily_usd` reached | Raise it in `factory.json`, or wait for tomorrow |

---

## Before you let other people use it

- **Use an API key** with a spend limit for work done for others; a personal
  Claude plan is for your own use.
- **Use a bot user, not an admin**, for `FACTORY_GITLAB_TOKEN`: Developer on the
  repositories it works on, nothing more. Issue text is untrusted input, and
  agents run commands.
- **Keep approvers to the people accountable** for what ships, and merging a
  person's decision.
