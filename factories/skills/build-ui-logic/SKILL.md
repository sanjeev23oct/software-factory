---
name: build-ui-logic
description: Maker skill: build UI logic, the functions that decide what is shown. Named by tasks in tasks.md.
applies_to: 
---
# build-ui-logic

Build exactly the one task you were given, as its lines in `tasks.md` and the design describe it. Read the engineering guide and two neighbouring files of the same kind first, and match them.

Logic is pure functions over data: filtering, sorting, counting, deciding state. It never touches the page and never reads the clock; anything that varies, such as today's date, is passed in. Export what the view and the page need. Add nothing the task did not ask for.

You are the maker. Do not tick the task, do not run the section's gate, and do not write evidence. Report what you built and anything the spec left undefined.
