# The test drive sandbox

A real factory run that leadership can drive themselves. They file an issue in
GitLab, and the factory on the VPS does the rest, in the open, on that issue:

1. **Within a minute**, a comment says the factory picked it up. A webhook
   starts a pass as soon as an issue is filed or someone comments, so nobody
   waits for the 10-minute schedule.
2. **A few minutes later**, the requirements are on the issue's branch, and a
   comment asks for `approve`.
3. **After `approve`**, agents plan the work and build it section by section.
   A separate checker session verifies each section, and a failed check goes
   back to a new maker with written findings. Each pass comments what happened,
   including every rejection.
4. **When every check passes**, a comment carries a **Try it** link to the
   change running in a browser, and asks for `approve` again.
5. **After the second `approve`**, the factory opens a merge request with the
   code, the tests, the specs and the evidence. Merging stays a person's call.

**Where each request stands** is at `/<project>/status/` on the preview host: a read-only page, in plain
words, with a button to each request's GitLab issue, its **Try it** link and, when done, its merge
request. It refreshes every minute. Approving stays on the issue.

A typical change takes 20 to 40 minutes of factory time, plus however long the
gates wait for a person.

To bring the factory to your own codebase, with its own stack, see
[docs/new-project.md](../docs/new-project.md) instead.

## What is in this folder

| Path | What it is |
| --- | --- |
| `app/` | The seed app: a small task board in plain HTML and JavaScript, with `node --test` tests and issue templates that label new issues `factory`. |
| `target/` | The rules agents follow on that app (`AGENTS.md`) and its checks (`presubmit`). |
| `preview/` | A small nginx container that serves `main` and each `factory/<item>` branch at `/<item>/`, refreshed every 20 seconds, on a hostname through Traefik or on a port. |
| `playground/` | An empty app for a client project (`playground/app/`) and its agent rules (`playground/target/`). |
| `setup.sh` | Sets all of it up on the VPS. Safe to run again. |
| `../factories/test-drive/` | The pipeline: read issue, requirements, **you**, tasks, lint, maker-checker build, evidence re-check, presubmit, preview, **you**, merge request. |

## Set it up on the VPS

You need an admin personal access token with the `api` scope
(GitLab: avatar → Edit profile → Access tokens).

    ssh root@194.164.148.19
    cd /opt/software-factory 2>/dev/null || git clone https://github.com/sanjeev23oct/software-factory.git /opt/software-factory && cd /opt/software-factory
    git fetch origin test-drive && git checkout test-drive
    GITLAB_TOKEN=glpat-... INVITE="ceo:ceo@example.com cto:cto@example.com" sandbox/setup.sh

`INVITE` is optional. It creates the GitLab users that do not exist yet,
prints each first password once, and adds everyone to the sandbox project as
Developer. Any member of the sandbox project may `approve`, so keep it
private and invite only the people taking the drive.

### A client project instead

To give a client their own project that starts as an empty page, with previews
under a hostname that the server's Traefik already routes:

    GITLAB_TOKEN=glpat-... SANDBOX_PROJECT=clients/<project> \
      SEED=sandbox/playground/app RULES=sandbox/playground/target \
      PREVIEW_HOST=factory.example.com AUTH_USER=<login name> \
      INVITE="<gitlab username>:<email>" sandbox/setup.sh

Run it once per client. Each project gets its own pipeline, named after the
project, and its own area on the preview server, `/<project>/`, with its
previews and its status page behind a login of its own. The script prints
that login, and the first GitLab password of anyone it creates, once: keep
them somewhere safe, never in this repository. The client sees only the GitLab
projects they are a member of.

To give the client their getting-started page, run
`python3 sandbox/onboarding.py --client <name> --project clients/<project>`.
It fills in [client-onboarding.md](client-onboarding.md) with their links and
writes `private/<name>-onboarding.md`, which git ignores. The page holds no
usernames or passwords; send those separately.

The script prints the link to file an issue and the client's status page.
Without `PREVIEW_HOST` previews are served on port 8090, and the script says
whether that port needs opening.

### What the script changes

- GitLab: creates group `sandbox` and private project `test-drive-app`, the
  `factory` label, a read-only token for the preview server, and a webhook on
  issues and comments.
- GitLab admin setting: adds `127.0.0.1` to the outbound allowlist, so that
  webhook can start a pipeline on the same GitLab. Nothing wider is opened.
- Factory project: adds `targets/test-drive/`, allows `trigger` pipelines in
  `.gitlab-ci.yml`, and sets `FACTORY_PREVIEW_URL`, `FACTORY_BOT_USER` and
  `FACTORY_REF`.
- VPS: starts the `factory-preview` container from `/data/factory-preview/`.

`FACTORY_REF` pins the factory code the runner clones. Setup sets it to the
commit you ran it from, because the progress comments, the preview stage and
the webhook guard are newer than `main`. Set it back to `main` once this work
is merged.

## Before the first executive drives it

Do one run yourself:

1. File "Add a search box that narrows the list as I type" with the Feature template.
2. Check that a pipeline starts in the factory project within a minute, and
   that the issue gets a progress comment and then the gate notice.
3. Reply `approve` (without a slash: GitLab swallows `/approve` on an issue), wait for the **Try it** link, and open it.
4. Reply `approve` again and check that the merge request opens.

## Reset between drives

Close or delete the issues and merge requests, and delete the `factory/*`
branches; the preview drops a branch within a minute of it going. To return the
app to its first state, force-push `sandbox/app/` to `main`, or delete the
project and run `setup.sh` again.

## Costs and limits

Agent runs use the Claude login in the factory project's
`CLAUDE_CODE_OAUTH_TOKEN`. The runner does one pass at a time, so two
executives filing at once are worked one after the other. A stage that fails
three times stops with a comment, and a maintainer decides what to do.
