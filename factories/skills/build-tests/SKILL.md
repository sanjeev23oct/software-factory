---
name: build-tests
description: Maker skill: write the automated tests for a section. Named by tasks in tasks.md.
applies_to: 
---
# build-tests

Build exactly the one task you were given, as its lines in `tasks.md` and the design describe it. Read the engineering guide and two neighbouring files of the same kind first, and match them.

Cover each acceptance criterion and each correctness property the section maps to: the success case and the obvious failure. A test must be able to fail: check it fails without the code it tests. Tests create and clean up their own data and never depend on today's date.

You are the maker. Do not tick the task, do not run the section's gate, and do not write evidence. Report what you built and anything the spec left undefined.
