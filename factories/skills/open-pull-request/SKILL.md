---
name: open-pull-request
description: Push the item branch to GitHub and open a pull request for a person to review and merge. A script; no judgment involved.
---
# open-pull-request

The factory runs `factory/scripts/open_pull_request.py`. It pushes `factory/<item>` and opens a pull request whose description closes the issue and links the requirements, tasks and every evidence file.

It uses the `gh` login on this machine. It never merges and refuses to push any branch that does not start with `factory/`. Reviewing and merging is a person's decision, made on GitHub.
