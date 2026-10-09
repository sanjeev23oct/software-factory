---
name: write-tech-spec
description: Write specs/GH<n>/tech.md, the tech spec for a feature issue. Use after the product spec exists.
---
# Write a tech spec

The tech spec says how the product spec will be met. Write it after
`product.md` and refer to its invariants by number.

Write `specs/<issue-id>/tech.md` with exactly these sections:

## Context
How the relevant code works today, with `path:line` references. Only what a
reader needs to judge the proposal.

## Proposed changes
Per file: what changes and why. Include any change to stored data and how
old data keeps loading. Name the alternative you rejected if there was a
real one.

## Testing and validation
For each invariant in `product.md`, the test that will prove it. Name the
test file and describe the case. Say what must be checked by hand, if
anything.
