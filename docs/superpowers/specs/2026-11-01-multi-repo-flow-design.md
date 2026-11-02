# One issue, several repositories

## Goal

A target may list additional GitLab repositories that an issue could need.
One issue remains one work item. Agents may inspect every listed checkout,
change the repositories needed for that issue, and leave the others untouched.
The original checkout remains the home for the issue, spec, and approval gates.

## Configuration

Existing `target.json` files keep their current single-repository behavior.
An optional `repositories` object maps short names to additional repositories.
Each entry declares a local `repo`, optional CI `remote`, `main`, GitLab `host`
and `project`, a `presubmit` command, protected path prefixes, and optionally
the name of a CI token variable. The target may declare an `integration` command
that checks the repositories together. Secrets stay in CI variables.

## Work item

Each listed repository gets its own worktree and a branch named
`factory/<target>-<item>-<repository>`. Agents receive the checkout names and
paths in their task. The factory checks changed files in every checkout against
that stage's write rules and that repository's protected paths. It commits
accepted changes separately. Only branches with commits are pushed.

## Verification and handoff

The target's existing verification stage still runs. When it passes, the
factory also runs the presubmit command of each changed additional repository.
If configured, it runs the joint integration command with paths to all
checkouts in environment variables. Before merge requests, the factory runs
the primary presubmit and all changed-repository checks again.
Failures stop handoff. The existing stage's `on_fail` route handles repair.

The primary merge-request stage keeps its current behavior when that branch
has commits. It skips an unchanged primary branch. The factory opens one GitLab
merge request for each changed additional repo.
Each request links the original issue. Repeated runs reuse open requests.
The factory never merges; a person reviews each request. Two GitLab merges
cannot be atomic, so cross-repository changes must remain compatible while
the requests are merged in sequence.

## Tests

Use small temporary Git repositories to test worktree isolation, changed-repo
selection, protected paths, checks, and repeatable branch publication. Mock
GitLab API calls for multi-request handoff. Keep the existing single-repo
tests and run `./script/presubmit`.
