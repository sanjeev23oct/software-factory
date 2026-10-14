---
name: build-ui
description: Maker skill: build one UI artifact when no more specific UI skill fits. Named by tasks in tasks.md.
applies_to: 
---
# build-ui

Build exactly the one task you were given, as its lines in `tasks.md` and the design describe it. Read the engineering guide and two neighbouring files of the same kind first, and match them.

Follow the visual spec exactly: text, states and `data-testid`s. Reuse existing components. Prefer the more specific skills (`build-ui-logic`, `build-ui-view`, `build-ui-page`) when the pipeline has them.

You are the maker. Do not tick the task, do not run the section's gate, and do not write evidence. Report what you built and anything the spec left undefined.
