---
name: review-request
description: Review a pull or merge request that passed the process check, against its requirements and the engineering guide.
---
# review-request

The process check has already passed, so the spec, evidence and tests exist. Your job is what a script cannot judge: is the code right?

Review `git diff origin/<main>...HEAD` in the checkout. Change no code. Write exactly one file at the checkout root: `factory_review.md`.

Read first: the spec folder the request touches (requirements, design if present, tasks, evidence), and the engineering guide the prompt names.

Check, in order:

1. Each acceptance criterion and correctness property in the requirements: find the code that satisfies it and the test that proves it. Name any that has neither.
2. Do the tests test the behavior, or only that the code runs? Flag tests that cannot fail.
3. Does each evidence file match what the code actually does?
4. Correctness: wrong status codes, missing validation, unhandled empty or missing values, behavior that differs from the design.
5. Anything changed that the requirement did not need.

Run the tests yourself where reading is not convincing.

## Output

```
## Code review: approve

Checked 6 acceptance criteria and 3 correctness properties. All have code and a test.

### Findings
- **Blocking** `path/to/file:42` what is wrong, and what to do
- **Suggestion** `path/to/file:10` ...
```

The heading is exactly `## Code review: approve` or `## Code review: changes requested`. Any blocking finding means changes requested. Write for the request's author: specific, short, no praise, no hedging. Do not ask for changes of taste.
