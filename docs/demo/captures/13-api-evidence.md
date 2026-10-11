Status: PASS

# Section 2 — Backend Gate Evidence

## Cat 1 — `loop/2-backend-checker.md` grep checks (run from repo root)

| Check | Expected | Actual | Result |
| --- | --- | --- | --- |
| `grep -c 'def parse_due' api/app.py` | 1 | 1 | PASS |
| `grep -c 'due must be a valid date in YYYY-MM-DD form' api/app.py` | at least 2 | 2 | PASS |
| `grep -c 'urlsplit' api/app.py` | at least 1 | 2 | PASS |
| `grep -c 'def handle(store, method, path, body=None, today=None)' api/app.py` | 1 | 1 | PASS |
| `grep -c 'overdue' api/app.py` | at least 2 | 2 | PASS |
| `grep -c 'due' README.md` | at least 2 | 3 | PASS |

Note on the previously-failing check: earlier attempts used a module-level `OVERDUE_PARAM` constant referenced by name, so the literal substring `overdue` appeared on only one line. The current code (`api/app.py` lines 43-44) uses a local variable instead — `overdue = query.get("overdue") == ["true"]` followed by `if overdue:` — so the literal word `overdue` now appears on two separate lines. This check now passes.

## Design/requirements verification — `api/app.py` tasks 2.1–2.5

Verified by direct code reading and live interpreter execution of `api.app.handle` / `api.app.parse_due` against fresh `TaskStore()` instances (script run from repo root with `sys.path` including `.`).

| Check | Expected | Actual | Result |
| --- | --- | --- | --- |
| 2.1 `parse_due(None)` | `(True, None)` | `(True, None)` | PASS |
| 2.1 `parse_due(20261101)` (non-str) | `(False, None)` | `(False, None)` | PASS |
| 2.1 `parse_due("11/01/2026")` (bad format) | `(False, None)` | `(False, None)` | PASS |
| 2.1 `parse_due("")` (bad format) | `(False, None)` | `(False, None)` | PASS |
| 2.1 `parse_due("2026-13-01")` (invalid calendar, month 13) | `(False, None)` | `(False, None)` | PASS |
| 2.1 `parse_due("2026-02-30")` (invalid calendar, Feb 30) | `(False, None)` | `(False, None)` | PASS |
| 2.1 `parse_due("2026-11-01")` (valid) | `(True, "2026-11-01")` | `(True, "2026-11-01")` | PASS |
| 2.2 `POST /tasks` with invalid `due` (AC 4.1–4.4) | `400` error; no task created; `store.create` never called | `(400, {"error": "due must be a valid date in YYYY-MM-DD form"})`; `store.all()` stayed `[]` | PASS |
| 2.2 `POST /tasks` with valid `due` (AC 1.1) | `201`, `store.create(title, due=due)` | `(201, {"id": 1, "title": "a", "done": False, "due": "2026-11-01"})` | PASS |
| 2.2 `POST /tasks` with `due` absent (AC 1.2) | `201`, `store.create(title, due=None)` | `(201, {"id": 2, "title": "b", "done": False, "due": None})` | PASS |
| 2.2 `POST /tasks` with `due: null` (AC 1.3) | `201`, `due: null` | `(201, {"id": 3, "title": "c", "done": False, "due": None})` | PASS |
| 2.3 `PATCH /tasks/<id>` with invalid `due` (AC 4.5, 4.6) | `400` error; stored `due` unchanged | `(400, {"error": "due must be a valid date in YYYY-MM-DD form"})`; task 1's stored `due` stayed `"2026-11-01"` | PASS |
| 2.3 `PATCH /tasks/<id>` with valid `due` (AC 3.1) | `200`, `changes["due"] = due` reflected in stored task | `(200, {"id": 1, "title": "a", "done": False, "due": "2026-12-25"})` | PASS |
| 2.3 `PATCH /tasks/<id>` with `due: null` (AC 3.2) | `200`, clears `due` | `(200, {"id": 1, "title": "a", "done": False, "due": None})` | PASS |
| 2.3 `PATCH /tasks/<id>` with `due` absent, only `title` patched (AC 3.3) | no `due` key in `changes`; stored `due` untouched | `(200, {"id": 2, "title": "bb", "done": False, "due": None})` — `due` unchanged from its prior value | PASS |
| 2.3 `PATCH /tasks/<unknown-id>` with valid `due` (AC 3.4) | `404 {"error": "no task with id <id>"}` | `(404, {"error": "no task with id 999"})` | PASS |
| 2.3 `PATCH /tasks/<unknown-id>` with invalid `due` | `400` (validated before the 404 lookup runs — same pre-existing ordering as `title`/`done`, present in `app.py` before this feature) | `(400, {"error": "due must be a valid date in YYYY-MM-DD form"})` | PASS (matches pre-existing pattern; AC 3.4 itself only specifies the valid-`due` case, which returns 404 as shown above) |
| 2.4 `handle` splits `path`/query via `urlsplit`/`parse_qs` once, before `/tasks` and `/tasks/<id>` routing checks | `/tasks/<id>` routing unaffected by the split | `handle(store, "GET", "/tasks/1", today=today)` → `(200, {...})` correctly routed to the single-task handler | PASS |
| 2.4 `handle(store, method, path, body=None, today=None)` defaults `today` to `datetime.date.today()` when omitted | works without explicit `today` | `handle(store, "GET", "/tasks")` (no `today` arg) → `200` with all tasks, no error | PASS |
| 2.4 `GET /tasks?overdue=true` filter (AC 5.1–5.4) | only tasks where `due is not None and due < today and done is False` | against `today=2026-10-11` with tasks due `2026-01-01`/not done, due `2026-01-01`/done, due `2026-10-11` (== today), and `due: null`: only the not-done task due before today (`id: 1`) was returned | PASS |
| 2.4 `GET /tasks` with no `overdue` param (AC 5.5) | unfiltered, same as `store.all()` | returned all 4 tasks regardless of `due`/`done` | PASS |
| 2.5 README documents `due` on `POST`/`PATCH` rows and `GET /tasks?overdue=true` | rows mention `due`; overdue row/note present | `POST /tasks` row: `` {"title": "...", "due": "YYYY-MM-DD"} `` (`due` optional); `PATCH /tasks/<id>` row: "Update `title`, `done`, or `due` (`null` clears it)"; dedicated row `GET \| /tasks?overdue=true \| List tasks whose due is before today and not done` | PASS |

## Cat 3 — full test suite

| Check | Expected | Actual | Result |
| --- | --- | --- | --- |
| `python3 -m unittest discover -s tests` | all pass, no regressions | `Ran 9 tests in 0.000s` / `OK` — all 9 existing tests pass | PASS |
