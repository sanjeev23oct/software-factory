---
name: write-visual-spec
description: Write visual-spec.md for UI work: every screen and state described precisely enough to build and to check.
---
# write-visual-spec

Write exactly one file: `<spec folder>/visual-spec.md`. Change nothing else.

Work from the mockups or screenshots attached to the requirement when there are any, and from the app's existing screens and component library otherwise. Say which you used.

For each screen:

- layout, top to bottom, naming the existing components to reuse
- exact visible text: headings, button labels, empty-state and error messages
- every state: loading, empty, populated, error, disabled
- a `data-testid` for each interactive element, so tests and checker greps can find it
- keyboard and focus behavior where it matters

Where no mockup settles a choice, pick the option closest to an existing screen and list it under **Needs clarification**.
