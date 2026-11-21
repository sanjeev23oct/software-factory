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
4. **Existing services used**: when the requirement touches anything cross-cutting (sending email,
   SMS, WhatsApp or push; documents and attachments; people or sewadar data; login, roles and
   permissions; files; workflows; audit; AI), the shared service from the organisation knowledge
   the prompt names, and what this work uses it for. If the knowledge has nothing that fits, put
   that under *Needs clarification*; never plan to build a new shared service.
5. **Out of scope**: what a reader might expect that this does not do.
6. **Needs clarification**: every choice the requirement leaves open. Do not guess silently. Omit the section when empty.

A human approves this file before anything else happens. It is the contract for every later stage.
