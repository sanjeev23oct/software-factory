---
name: process-check
description: Check that a pull or merge request followed the team's process: spec, skills, evidence, tests, standards. A script; no judgment involved.
---
# process-check

The factory runs `factory/scripts/check_mr_process.py` with the rules in this factory's `process.json`. Edit those rules in the factory editor, under Review rules.

It checks that code came with a spec, that every task names a skill, that ticked work has evidence, that tests changed with the code, that no secret was added, and whatever rules the team has added.

A request that fails is not handed to the review agent. The report is posted, and the review runs after the next push.
