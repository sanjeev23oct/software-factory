---
name: build-db
description: Maker skill: build one database change (a table, a column, a stored function) named by a task in tasks.md.
---
# build-db

Build exactly the one task you were given, as its lines in `tasks.md` and the design describe it. Read the engineering guide and two neighbouring files of the same kind first, and match them.

Add a new migration; never edit one that already exists. Include its rollback. Do not apply it to any shared database.

You are the maker. Do not run the section's gate, do not write evidence, and do not tick the box. Report what you built and anything the spec left undefined.
