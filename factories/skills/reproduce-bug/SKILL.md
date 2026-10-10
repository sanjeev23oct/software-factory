---
name: reproduce-bug
description: Reproduce a reported bug with a failing automated test before anything is fixed.
---
# reproduce-bug

1. Read `issue_context.md`. Separate what the reporter saw from their guess at the cause.
2. Find the code path. Reproduce the wrong behavior.
3. Write one automated test that fails because of the bug, in the repository's existing test style. Run it and watch it fail for the right reason.
4. Write `<spec folder>/reproduction.md`: the steps, the failing test's name and output, and the root cause as `path:line` with your confidence.

Change no product code. If you cannot reproduce it, write what you tried and exactly what you need from the reporter, and stop. Do not guess at a fix.
