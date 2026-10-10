# Engineering guide for factory agents

Replace this file with your repository's rules. Agents read it before every task.

## What this repository is

One paragraph: what the product does, and the stack.

## Where the rules live

Point at the documents agents must follow: coding standards, architecture notes, the contributing guide. Say which wins when they disagree.

## Rules

- What must never be done (for example: no new dependencies without a stated reason, never edit an applied migration).
- What agents may not touch. Keep this in step with `protected` in `target.json`.
- Nothing leaves this machine: no push, no merge request, no deployment.

## Verification

What `presubmit` runs, and what it cannot check.
