## Process check: does not follow the process

2 failed, 3 to look at, 1 passed. Checked by script against `origin/main`.

| | Check | Detail |
| --- | --- | --- |
| ⚠️ | Linked to an issue | the description names no issue |
| ❌ | Spec before code | 1 code file(s) changed but nothing under `specs/` was touched |
| ❌ | Automated tests for api changes | 1 api file(s) changed, no test file under `tests/` |
| ✅ | No secrets |  |
| ⚠️ | No print statements in the API | `app.py` |
| ⚠️ | API changes update the README | changed `app.py` but nothing under `README.md` |

The code was not reviewed. Fix the failed checks first, then the review runs on the next push.
