---
name: build-ui-view
description: Maker skill: build UI view code, the markup for a piece of the screen. Named by tasks in tasks.md.
applies_to: 
---
# build-ui-view

Build exactly the one task you were given, as its lines in `tasks.md` and the design describe it. Read the engineering guide and two neighbouring files of the same kind first, and match them.

A view turns data into markup. Use the exact visible text, states and `data-testid`s the spec gives. Escape any text that came from data. Show state in words as well as colour. Reuse existing components and classes before adding new ones.

When `<spec folder>/reference/` has a screenshot for this screen, open it and its contract (`<screen>.json`) first. Match its layout, spacing, type and colour, and give each region the `data-testid` or id the contract names: a checker measures the built screen against it.

You are the maker. Do not tick the task, do not run the section's gate, and do not write evidence. Report what you built and anything the spec left undefined.
