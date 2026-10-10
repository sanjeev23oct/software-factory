---
name: post-review
description: Post the process report and the code review as one comment on the request. A script; no judgment involved.
---
# post-review

The factory runs `factory/scripts/post_mr_note.py`. A previous factory comment on the same request is edited in place, so each request carries one comment. It comments only: it never approves, merges, or changes labels.
