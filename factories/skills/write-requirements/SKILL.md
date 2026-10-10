---
name: write-requirements
description: Write requirements.md for a work item: user stories with numbered, testable acceptance criteria.
---
# write-requirements

Write exactly one file: `<spec folder>/requirements.md`. Change nothing else.

Read `issue_context.md`, then the code the requirement touches, before writing.

## Structure

1. **Overview**: two or three sentences, and what you read as evidence (files, existing behavior).
2. **User stories**: As a / I want / So that, each with numbered acceptance criteria (`AC 1.1`, `AC 1.2`). Every criterion is one statement someone can check without reading the code: the exact input, the exact result, the exact error text.
3. **Correctness properties**: invariants that must always hold. These become tests and checker greps.
4. **Out of scope**: what a reader might expect that this does not do.
5. **Needs clarification**: every choice the requirement leaves open. Do not guess silently. Omit the section when empty.

A human approves this file before anything else happens. It is the contract for every later stage.
