---
name: build-tasks
description: Maker: build one section of tasks.md, using the skill each task names. Never ticks a task or writes evidence.
---
# build-tasks (the maker)

You are the maker. The prompt names one section of `<spec folder>/tasks.md`. Build that section and stop.

1. Read the requirements, the design if there is one, and the section you were given.
2. For each unticked task in the section, in order:
   - Open the skill the task names (`→ run: /skill`) in this pipeline's skills folder and follow it.
   - Build exactly what the task and its sub-items say. Where the spec leaves a detail out, stop and say so; do not invent it.
3. Run the presubmit command the prompt names. It must pass.
4. Report what you built, file by file.

## What you must not do

- Do not tick any box in `tasks.md`.
- Do not write anything under `evidence/`.
- Do not run the section's gate and report it as passed.

A checker in a separate session, which has not seen you work, will run the gate against what you built and write the evidence. The factory rejects a maker that ticks tasks or writes evidence.

If `factory_feedback.md` exists, the checker or a script rejected the last attempt at this section. Fix every finding in it first. If a finding says a check in `loop/` is itself wrong, correct that check and say why.
