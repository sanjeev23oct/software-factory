---
name: publish-preview
description: Print the address where the pushed branch can be tried in a browser. A script; no judgment involved.
---
# publish-preview

The factory runs `factory/scripts/preview_link.py`. It prints `Try it: <address>`
for the item's branch, built from `FACTORY_PREVIEW_URL`. The factory puts that
link in its progress comment and in the gate notice, so the person at the next
gate can use the change before approving it.

A preview server, such as the one in `sandbox/preview/`, serves each pushed
`factory/*` branch at that address. With no `FACTORY_PREVIEW_URL` set, the
stage passes and says there is no preview.
