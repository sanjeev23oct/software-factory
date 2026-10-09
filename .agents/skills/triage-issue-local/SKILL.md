---
name: triage-issue-local
specializes: triage-issue
description: Repo-specific triage guidance for tasklite. Only the categories the core triage-issue skill marks as overridable are specialized here.
---

# Repo-specific triage guidance for `tasklite`

This is a companion to `triage-issue`. It does not change the output schema
or the safety rules.

## Repro defaults

- `tasklite` is a local CLI with no network and no dependencies, so most bug
  reports can be reproduced directly. Try before you ask.
- Always pass `--db` pointing at a fresh file under `$TMPDIR`. Never run
  against the default `tasks.json`.
- Report `high` only when you saw the wrong behavior yourself.

## Label guidance

- `area:storage` for ids, the task file, loading and saving.
- `area:cli` for flags, output format, error text, and exit codes.
- `area:docs` for README and `--help` text.

## Readiness guidance

- Recommend `ready-to-implement` for a bug only when you reproduced it and
  the fix looks narrow. Otherwise recommend `needs-info`.
- Recommend `ready-to-spec` for a feature whose need is clear but which
  leaves user-visible choices open: flag names, output format, error text,
  or anything stored in the task file.

## Follow-up patterns

- No commands in the report: ask for the exact commands run and the output.
- "Sometimes" with no pattern: ask what differs between a working run and a
  failing one.
- Ask at most 2 questions per triage.
