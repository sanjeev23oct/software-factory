---
name: verify
description: Run the repository's presubmit: build, lint and tests. A script; no judgment involved.
---
# verify

The factory runs the target's `presubmit` script from the checkout root. It must exit 0. Put every check a change must pass in that script: build, typecheck, lint, unit and integration tests.

On failure the factory sends the output back to the stage that did the work.
