Verdict: APPROVE

## Findings
- [suggestion] api/app.py:27 `parse_due`'s regex rejects non-string input via short-circuit `or` (`not isinstance(...) or not re.match(...)`), which is correct but relies on evaluation order being non-obvious at a glance; a one-line comment would save the next reader a double-take. Not blocking.
