---
name: write-tech-spec
description: Write specs/GH<n>/tech.md for a feature issue after reading the product spec and the code. Use after product.md exists, or when asked for a tech spec or implementation plan.
---

# write-tech-spec

The tech spec turns product intent into an implementation plan that fits the
code as it is. Write it after `product.md` and refer to its invariants by
number instead of restating them.

Write to `specs/GH<issue-number>/tech.md`.

## Research first

Read `product.md`, then the code. Identify the files, data flow, and
ownership boundaries involved. Do not guess at the current design when you
can read it. Record the commit you researched (`git rev-parse --short HEAD`)
and cite code as `path:line @ <sha>`.

## Structure

Required:

1. **Context**: how the affected code works today, with pinned references.
   Only what a reader needs to judge the plan.
2. **Proposed changes**: per file, what changes and why. New functions,
   flags, and stored fields. How data written by earlier versions keeps
   loading. Name the alternative you rejected when there was a real one.
3. **Testing and validation**: for each invariant in `product.md`, the test
   or check that proves it. Name the test file and the case. Say what must
   be checked by hand.

Optional, omitted when empty:

- **Risks and mitigations**: real failure modes or migration hazards.
- **Follow-ups**: deferred work worth naming.

## Length

Right-size it. A single-module change with a clear approach is under 40
lines. If Context and Proposed changes describe the same code twice,
collapse them.

## Keep the spec current

If implementation departs from the plan, `tech.md` is updated on the same
branch so it describes what ships.
