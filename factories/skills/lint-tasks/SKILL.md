---
name: lint-tasks
description: Check that tasks.md is fit for the maker-checker loop. A script; no judgment involved.
---
# lint-tasks

    python3 <factory>/factory/scripts/lint_tasks.py <spec folder>/tasks.md --skills-dir <skills folder>

It fails when a task names no skill, names a skill that does not exist, or a section lacks a gate with Cat 1, Cat 2, Cat 3 and an evidence file. On failure the factory sends the findings back to `write-tasks`.
