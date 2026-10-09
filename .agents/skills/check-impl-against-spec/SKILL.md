---
name: check-impl-against-spec
description: Compare a branch's implementation against the specs in spec_context.md and feed material mismatches into review.json. Use during review when spec context exists.
---

# Check implementation against spec

Use only when `spec_context.md` exists. This supplements the code review. It
does not produce a separate file.

## Process

1. Extract the concrete commitments from `spec_context.md`: every numbered
   behavior invariant, the files or subsystems the tech spec says change,
   stated constraints, and required tests or compatibility steps.
2. For each invariant, find the code that establishes it and the test that
   proves it. Exercise the product yourself where the test is missing or
   unconvincing.
3. Accept small implementation differences that preserve the spec's intent:
   naming, structure, technique.
4. Flag a mismatch only when it is material:
   - a required behavior is missing or wrong
   - the implementation contradicts a spec decision
   - the change adds significant unplanned scope
   - a required test or compatibility step is absent
   - the code and the checked-in spec disagree and the spec was not updated

## Output

Fold findings into `review.json`. Material drift is at least
`⚠️ [IMPORTANT]`. Tie a finding to changed lines when you can, otherwise put
it in `body`. State in `body` how many invariants you checked and how many
hold. Do not add comments merely to note alignment.
