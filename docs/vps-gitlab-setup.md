# The factory on a self-hosted GitLab

A record of the GitLab + runner setup built on the VPS at `194.164.148.19`
on 2026-10-27, and how to operate it. Nothing in this flow runs on a laptop.

A ticket filed in GitLab is picked up on a schedule, worked by Claude agents
on a GitLab runner, and stopped at a human gate you answer with a comment.

---

## What is running

All of it is Docker on the one VPS, alongside the sites that were already
there. Nothing was taken away from them: GitLab never binds port 80 or 443.

| Container | Image | Job |
|---|---|---|
| `gitlab` | `gitlab/gitlab-ce:17.11.3-ce.0` | GitLab itself |
| `gitlab-runner` | `factory-runner:17.11` (built here) | runs the factory's passes |
| `gitlab-tls` | `nginx:alpine` | terminates TLS for GitLab inside the box |

Files on the VPS:

| Path | Holds |
|---|---|
| `/data/gitlab/compose.yml` | GitLab's definition |
| `/data/gitlab/{config,logs,data}` | GitLab's state — **this is the backup target** |
| `/data/gitlab-runner/compose.yml` | the runner's definition |
| `/data/gitlab-runner/Dockerfile` | the runner image recipe |
| `/data/gitlab-runner/config/config.toml` | the runner's registration |
| `/data/gitlab-tls/` | the TLS proxy's config and self-signed certificate |

### How a browser reaches it

    you → Cloudflare (TLS) → VPS:80 → berth-proxy → coolify-proxy → gitlab:80

GitLab is at [gitlab.justpush.cloud](https://gitlab.justpush.cloud). It sits
behind the same chain as the other sites on the box, matched by hostname.

---

## The projects

| Project | What it is |
|---|---|
| `ai-sdlc/software-factory` | the **factory project**: holds `targets/`, the CI job, and the progress branch |
| `root/demo-app` | a tiny Python calculator, the product being worked on |
| `root/ci-smoke` | an empty leftover from an early runner test; safe to delete |

The factory project's `factory-state` branch is the factory's memory between
passes. The runner starts empty every time and restores from there.

---

## The credentials

Values are not written down here. These are the places they live.

| Where | What |
|---|---|
| GitLab → Settings → CI/CD → Variables, on `ai-sdlc/software-factory` | `FACTORY_GITLAB_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN` |
| `/data/gitlab-runner/config/config.toml` | the runner's `glrt-` token |
| `/data/gitlab/config/initial_root_password` | the first root password; GitLab deletes it 24h after first boot |

Reset the root password if that file is gone:

    ssh root@194.164.148.19 'docker exec -it gitlab gitlab-rake "gitlab:password:reset[root]"'

**Rotate the two tokens that were pasted into a chat**: the GitLab admin
token `glpat-…` and the runner token `glrt-…`. The runner one resets under
Admin Area → CI/CD → Runners → the runner → Reset token, and then needs
re-registering with the command in the next section.

---

## How a pass is triggered

    GitLab's clock → pipeline → runner picks it up → ci_tick.sh → one pass

| Part | Where it lives |
|---|---|
| the schedule, `*/10 * * * *` Asia/Kolkata | inside GitLab, Build → Pipeline schedules |
| the job | `.gitlab-ci.yml` in the factory project |
| the work | `factory/scripts/ci_tick.sh` in the factory code |

The job only answers the schedule and the "Run pipeline" button. A git push
does **not** start a pass, so editing `targets/` is safe.

The factory code is not stored in the factory project. Each pass clones it
fresh from `https://github.com/sanjeev23oct/software-factory.git`, pinned by
the `FACTORY_REF` variable.

---

## The demo-app pipeline

Defined in `targets/demo-app/factory.json`, nine stages:

    read-issue → reproduce → fix → verify → review → check-review
      → [you: approve-fix] → pull-request (off) → merge-request

| Stage | By | Produces |
|---|---|---|
| read-issue | script | picks up issues labelled `factory` |
| reproduce | agent | a failing test, `reproduction.md` |
| fix | agent | the change |
| verify | script | runs `targets/demo-app/presubmit`; failure sends it back to `fix` |
| review | agent | `review.md` with a verdict |
| check-review | script | failure sends it back to `fix` |
| approve-fix | **human** | reply `/approve` on the issue |
| merge-request | script | opens the MR |

Three tries per stage, then the item is blocked for a person.

### Answering a gate

The factory comments on the issue when it needs you. Reply `/approve` on that
issue, from a browser or phone. Only replies written after the gate opened
count, and only from the people in `approvers`.

---

## Proven run, 2026-10-27

Issue [demo-app #1](https://gitlab.justpush.cloud/root/demo-app/-/issues/1):
`divide()` crashed with a bare `ZeroDivisionError`.

One pass, about three minutes of runner time, carried it from the ticket to
the gate. The agent wrote a failing test first, then the guard:

```python
def divide(a, b):
    if b == 0:
        raise ValueError("cannot divide by zero")
    return a / b
```

The review agent approved it and raised one suggestion of its own — that the
test checks the exception type but not its message. Branch `factory/GL1`,
stopped at `approve-fix`.

Agent cost for the whole run was a few cents.

---

## Four things that had to be fixed

These are worth knowing, because three of them will bite again on any new
repository pointed at this factory.

### 1. Nothing listens on 443 inside the VPS

Cloudflare terminates TLS and talks to the box on port 80 only. Inside
Docker, `gitlab.justpush.cloud` resolves to the GitLab container, which also
serves plain HTTP. So any `https://gitlab.justpush.cloud` call from inside the
box hit a closed port.

Two parts to the fix. The runner's own git checkout is told to use the
internal name, in `/data/gitlab-runner/config/config.toml`:

    clone_url = "http://gitlab"

And an nginx container terminates TLS at a fixed address for everything else,
with a self-signed certificate baked into the runner image's trust store.

### 2. Cloudflare blocks Python

Going out through Cloudflare instead was tried first. It answers urllib's
default user agent with `error 1010: Access denied`. The factory's scripts
build `https://` URLs with no way to override the scheme, so the runner's
hosts file pins the name to the local TLS proxy and skips Cloudflare:

    extra_hosts:
      - "gitlab.justpush.cloud:10.0.1.250"

### 3. Agents could not read their own skills

**This is a real bug in the factory, not just this box.** The factory runs
each agent with `--add-dir <factory code>`, but `ci_tick.sh` expects
`targets/` at `$PWD/targets`, outside that directory. So an agent told
"read the skill at `…/targets/demo-app/skills/reproduce-bug/SKILL.md`" could
not open it, and gave up in a single turn — a run that cost 1.5¢ instead of
5¢ and wrote nothing.

Worked around in `.gitlab-ci.yml` by copying `targets/` inside the factory
code before the pass:

    cp -r "$CI_PROJECT_DIR/targets" "$CI_PROJECT_DIR/.factory-code/targets"
    FACTORY_TARGETS_DIR: $CI_PROJECT_DIR/.factory-code/targets

Anyone following `docs/run-in-gitlab.md` as shipped will hit this.

### 4. Bytecode files broke the review stage

Running the tests left `__pycache__/*.pyc` in the checkout, and the review
stage rejects files it is not allowed to write. Fixed with a `.gitignore` in
`demo-app` and `PYTHONDONTWRITEBYTECODE: "1"` in the job.

---

## Pointing a new repository at this factory

1. Clone it locally, then `python3 factory/flow.py init <name> --sample <sample> --repo <path>`.
2. In `targets/<name>/target.json`, add a `remote` clone URL. Without it the
   runner has nothing to clone — the local `repo` path does not exist there.
3. In `targets/<name>/factory.json`, set `source` to the real host, project and
   label, list the `approvers`, and set `"auto": true`.
4. Replace `targets/<name>/presubmit` with the repository's real build and test
   commands. The sample stub always fails, which blocks the `verify` stage.
5. Commit `targets/<name>/` into the factory project and push.
6. Check it: `python3 factory/flow.py --target <name> validate`.

Files pushed through GitLab's API arrive non-executable. `presubmit` needs the
execute bit set, or `verify` cannot run it.

---

## Running the app itself in a job

The current runner uses the **shell** executor, so a job runs directly in the
runner container. That suits a repository whose tests need nothing but
python3, node and git, which are in the image.

A repository that needs its real stack — a database, a browser, the whole
compose file — needs the **docker** executor with its own private docker
daemon. Do not hand the job the host's docker socket: a job could then stop
`gravics`, `gymflash` and the rest.

The right shape is for `presubmit` itself to bring the stack up and down, so
the same one script works on a laptop and on the runner:

    compose up -d → wait healthy → tests → compose down -v

---

## Health and limits

| | |
|---|---|
| RAM, GitLab | about 4 GB, always on |
| RAM, runner idle | about 100 MB |
| RAM, a running job | 1–2 GB |
| Jobs at once | 1 (`concurrent = 1`) |
| Cores on the box | 4, shared with the live sites |
| First boot | about 12 minutes; normal, it builds its database |

Claude usage is shared with the account that made `CLAUDE_CODE_OAUTH_TOKEN`.
When a limit is reached the work pauses without spending an attempt, and a
later pass carries on.

### Common checks

    ssh root@194.164.148.19 'docker ps --filter name=gitlab'
    ssh root@194.164.148.19 'docker exec gitlab-runner gitlab-runner list'
    ssh root@194.164.148.19 'docker logs gitlab --tail 30'

The full audit trail of every stage, session and cost is
`demo-app/events.jsonl` on the factory project's `factory-state` branch.

---

## Undo

Removing GitLab and the runner, and nothing else on the box:

    ssh root@194.164.148.19 'docker compose -f /data/gitlab/compose.yml down'
    ssh root@194.164.148.19 'docker compose -f /data/gitlab-runner/compose.yml down'
    ssh root@194.164.148.19 'docker compose -f /data/gitlab-tls/compose.yml down'

That stops them and keeps the data. Adding `-v`, or deleting `/data/gitlab`,
destroys every repository, issue and setting with no way back.
