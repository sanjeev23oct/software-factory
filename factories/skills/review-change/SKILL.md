---
name: review-change
description: Review a work item's branch against its requirement and write a verdict a script can read.
---
# review-change

Review `git diff <main>...HEAD` in the checkout. Change no code. Write exactly one file: `<spec folder>/review.md`.

Check, in order:

1. Does the change do what the requirement asks? For a bug, is the root cause fixed?
2. Is there a test that fails without the change and passes with it?
3. Does it follow the engineering guide the prompt names?
4. Is anything changed that the work did not need?

Run the product and the tests where reading is not convincing.

## Output

```
Verdict: APPROVE

## Findings
- [blocking] path/to/file:42 what is wrong and what to do
- [suggestion] ...
```

The first line is exactly `Verdict: APPROVE` or `Verdict: REJECT`. Any blocking finding means REJECT. Do not reject for style you would merely have written differently.
