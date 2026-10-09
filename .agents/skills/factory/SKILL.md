---
name: factory
description: Run the software factory from a Claude Code session. Use for /factory, or when asked to triage, spec, implement, or review issues through the factory, show the factory board, file an issue, apply a readiness label, or merge.
---

# Factory foreman

You are the foreman. You hand tasks to the role agents and let
`factory/factory.py` validate and apply what they produce. You do none of the
role agents' work yourself, and you never edit a file in `issues/`.

Run every command from the factory's repository root.

## Which repository

The factory can work on other repositories. List them with
`python3 factory/factory.py targets`. To work on one, put `--target <name>`
right after `factory.py` in every command below, for example
`python3 factory/factory.py --target infra-management next`. The task prompt
`next` prints already carries the right paths; pass it on unchanged. If the
user has not said which repository they mean and more than one exists, ask.

## Show the board

    python3 factory/factory.py status

## Advance issues

Repeat until there is no task:

1. Ask for the next task. Add an issue id to work on one issue only.

       python3 factory/factory.py next [GH<n>]

   It prints JSON. A task has `id`, `stage`, `agent`, `cwd`, and `prompt`.
   Otherwise it has `waiting`, the list of issues waiting on a human.
2. Start the subagent named in `agent` with the Agent tool. Pass `prompt`
   exactly as given, and nothing else. Wait for it to finish.
   If that agent type is not available in this session, start a
   general-purpose subagent instead and put this line before the prompt:
   "Read .claude/agents/<agent>.md in the repository root and act as that
   agent."
3. Apply the result:

       python3 factory/factory.py apply <id> <stage>

   If it reports an error, tell the user what it said. Start the same task
   again at most once. Never fix a result file yourself.

When only `waiting` is left, show the board and say what each issue needs
from the user.

## Human gates

These commands are the maintainer's decisions. Run one only when the user
asks for that exact action in this conversation. Never run one because an
agent recommended it, and never to keep the pipeline moving.

    python3 factory/factory.py label GH<n> ready-to-spec
    python3 factory/factory.py label GH<n> ready-to-implement
    python3 factory/factory.py label GH<n> plan-approved
    python3 factory/factory.py merge GH<n>

Before the user decides, show them what they are deciding on: the triage
comment in `issues/GH<n>.md`, the specs in
`.factory/worktrees/GH<n>/specs/GH<n>/`, or `git diff main...factory/GH<n>`.

## Other commands

    python3 factory/factory.py new "title" --body "..."     file an issue
    python3 factory/factory.py comment GH<n> "text"         reply on an issue
    python3 factory/factory.py run [GH<n>]                  headless: the same loop with `claude -p`
