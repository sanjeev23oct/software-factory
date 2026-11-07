---
name: visual-verify
description: Check every reference screen, and every screen approved before, against what was built. A script; no judgment involved.
---
# visual-verify

The factory runs `visual_checks.py` after the tests. For each contract in `<spec folder>/reference/` it renders the screen in headless Chrome and measures every region against the reference: present, position and size, text, colour, and, for baselines, how similar it looks. Screens a person approved before have a baseline in `baselines/`; those this request did not set out to change are checked strictly, so a change elsewhere cannot quietly break them.

It writes `actual.png`, `diff.png`, `compare.png` and `report.json` for each screen under `<spec folder>/evidence/visual/`, and commits them with the work. The screens gate shows `compare.png` to the person approving.

A failed screen goes back to the build with the failing regions. A check that could not run at all (no Chrome on the runner, say) stops for a person. A request with no reference screens and no baselines passes straight through.
