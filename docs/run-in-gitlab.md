# Run the factory in GitLab

The factory can run on a GitLab runner on a schedule, with nothing running on
your machine. You approve gates by replying `/approve` on the issue, from the
browser or the GitLab app.

## How it works

Every ten minutes a scheduled pipeline runs one pass:

1. It restores the factory's progress from the `factory-state` branch of your factory project.
2. For each pipeline that is switched on, it:
   - picks up new issues that carry the label and are assigned to the right person;
   - applies any `/approve` replies;
   - runs the agents until a person is needed;
   - pushes the `factory/*` work branches;
   - comments on the issue when a gate opens.
3. It saves the progress back to `factory-state`.

The runner starts empty each time. Everything the next pass needs is on the
`factory-state` branch or on the work branches.

## What you need

| | |
|---|---|
| A **factory project** | A private GitLab project that holds your pipelines (`targets/`) and the factory's progress. |
| A **GitLab token** | It must be able to read issues, comment, push `factory/*` branches and open merge requests on each repository the factory works on, and push to the factory project. Use a bot user or a group access token with the Developer role and the `api` and `write_repository` scopes. |
| A **Claude login** | Your Claude subscription (`claude setup-token`) or an Anthropic API key. |
| A **runner** | It must be able to reach `api.anthropic.com`, `registry.npmjs.org` and wherever the factory code is cloned from. |

## Set it up

1. **Create the factory project** in GitLab, private, for example `group/software-factory`.

2. **Add your pipelines.** Copy `targets/<name>/` from your machine into the project's `targets/` folder.
   In each `target.json`, set `remote` to the repository's clone URL. The runner clones from it.
   In each `factory.json`, say who may approve:

   ```json
   "target.json":  { "remote": "https://gitlab.example.com/group/repo.git", "main": "main", ... }
   "factory.json": { "source": { "type": "gitlab", "host": "gitlab.example.com", "project": "group/repo",
                                 "label": "factory", "assignee": "you", "approvers": ["you", "your-lead"] },
                     "auto": true, ... }
   ```

   To edit pipelines with the editor, point it at the project's checkout, then commit and push:

   ```sh
   FACTORY_TARGETS_DIR=~/code/software-factory-project/targets python3 factory/editor.py
   ```

3. **Add the job.** Copy [`factories/ci/gitlab-ci.yml`](../factories/ci/gitlab-ci.yml) to the project as `.gitlab-ci.yml`.

4. **Add the CI/CD variables** (Settings → CI/CD → Variables). Make both masked and protected.

   | Variable | Value |
   |---|---|
   | `FACTORY_GITLAB_TOKEN` | the GitLab token |
   | `CLAUDE_CODE_OAUTH_TOKEN` | the output of `claude setup-token` on your machine. Or set `ANTHROPIC_API_KEY` instead; set only one, because an API key takes precedence and is billed per token. |

5. **Schedule it** (Build → Pipeline schedules → New schedule). Use interval `*/10 * * * *`, branch `main`.
   Press the play button once to run a pass straight away.

6. **Stop the job on your machine**, if one is running: `python3 factory/scripts/schedule.py remove`.
   Two factories that do not share progress would both take the same issues.

## Approve a gate

When work reaches a gate, the factory comments on the issue:

> **The factory is waiting for you** at `approve-requirements`.
> Read first: [requirements.md](#)
> To approve, reply `/approve`. To approve and skip an optional stage: `/approve skip visual-spec`.

Reply `/approve`. The next pass, within ten minutes, carries on.

Only people listed in `approvers` count, or the `assignee` if there is no list.
Only replies written after the gate opened count, so an old `/approve` cannot pass a later gate.
Anyone else's reply is ignored.

## See what it is doing

- The **issue**: the gate comments and, at the end, the merge request.
- The **pipeline's job log**: one block per pipeline, per pass.
- The **`factory-state` branch**: `<pipeline>/events.jsonl` is the full audit trail, with every stage, session, approval and cost.

## Limits and costs

- **Usage limits.** On a Claude subscription, the factory shares your usage limits.
  When a limit is reached, the work pauses without using up an attempt, and a later pass carries on.
  The pipeline's `daily_usd` and `run_usd` still cap how much work a day may do.
- **Runner time.** Runner minutes on your own runners cost nothing.
  A feature takes about 15 to 20 minutes of runner time from start to merge request.
- **Merging.** The factory never merges. A person merges the merge request.
