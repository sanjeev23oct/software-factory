## Process check: follows the process

0 failed, 0 to look at, 11 passed. Checked by script against `origin/main`.

| | Check | Detail |
| --- | --- | --- |
| ✅ | Linked to an issue |  |
| ✅ | Spec before code | `1-tasks-need-a-due-date` |
| ✅ | Every task names a skill |  |
| ✅ | All tasks ticked |  |
| ✅ | Ticked work has evidence |  |
| ✅ | Spec-adherence checks hold | 8 of 8 re-run by script passed; 0 left to a checker |
| ✅ | No unplanned code |  |
| ✅ | Automated tests for api changes | 2 test file(s) changed |
| ✅ | No secrets |  |
| ✅ | No print statements in the API |  |
| ✅ | API changes update the README |  |
## Code review: approve

Checked 21 acceptance criteria and 5 correctness properties against `requirements.md`. All have code in `api/app.py`/`api/store.py` and a test in `tests/test_app.py`/`tests/test_store.py`. Ran `python3 -m unittest discover -s tests`: 28 pass. Diff is scoped exactly to the feature (`api/app.py`, `api/store.py`, `README.md`, tests) — no unrelated changes.

Spot-checked beyond the tests:
- `parse_due` correctly rejects dates with trailing whitespace/newline and zero month/day (`fromisoformat` raises even though the regex's `$` would otherwise let a trailing `\n` through).
- Query-string handling (`urlsplit`/`parse_qs`) doesn't break `/tasks/<id>` routing when a stray query string is present.
- Evidence files' claimed outputs match what the code actually does.

No findings.
