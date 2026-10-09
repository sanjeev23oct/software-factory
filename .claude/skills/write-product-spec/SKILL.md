---
name: write-product-spec
description: Write specs/GH<n>/product.md, the product spec for a feature issue. Use when an issue is ready-to-spec.
---
# Write a product spec

The product spec says what the user will see. It contains no implementation
detail: no function names, no file names, no data structures.

Write `specs/<issue-id>/product.md` with these sections:

## Problem
Two to four sentences. Who needs this and what they cannot do today. Link
the issue id.

## Behavior
A numbered list of invariants. This is the heart of the spec. Each one:

- is a single testable statement about observable behavior,
- gives the exact command, output, or error text where one applies,
- can be checked by someone who has never seen the code.

Cover the main path, then every edge: bad input, empty state, and how the
feature meets data written before the feature existed.

## Out of scope
What a reader might expect that this does not do.

## Open questions
Choices you made that the maintainer may want to overrule. One line each,
with the invariant number it affects. Write "None" if there are none.
