---
name: fix-bug
description: Fix a reproduced bug at its root cause, keeping the change as small as the bug.
---
# fix-bug

`<spec folder>/reproduction.md` names the failing test and the root cause.

- Fix the root cause, not the reported symptom. Check for the same mistake in sibling code and say what you found.
- The failing test must pass. Do not weaken or delete it.
- Change only what the bug needs. No refactoring, no unrelated cleanup.
- Add to `<spec folder>/reproduction.md` a short **Fix** section: what changed and why it is the root cause.

If `factory_feedback.md` exists, a check or a review rejected your last attempt. Address every point in it.
