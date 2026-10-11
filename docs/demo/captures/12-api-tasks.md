# Tasks: Tasks need a due date

## Section 1 — Data (`api/store.py`)

Satisfies: AC 1.2, AC 2.4, correctness property "every task has a `due` key"

- [x] 1.1 `TaskStore.create(title, due=None)`                        → run: `/build-backend`
  - [x] 1.1.1 signature per `design.md` § Data: `create(self, title, due=None)`
  - [x] 1.1.2 returned (and stored) task dict is `{"id": ..., "title": title, "done": False, "due": due}`
  - [x] 1.1.3 every existing call site that only passes `title` keeps working, with `due` defaulting to `None` (tasks created before this change keep working)
  - [x] 1.1.4 `TaskStore.update` is left unchanged — `due` flows through the existing `**changes` mechanism, same as `title`/`done`

### 1.X — Gate

> **CHECKER (Cat 1):** every check in `loop/1-data-checker.md` returns its EXPECTED value.
> **CHECKER (Cat 2):** write `evidence/1-data-gate.md` as a tick sheet.
> **CHECKER (Cat 3):** run `python3 -m unittest discover -s tests`; EXPECTED: all pass.

## Section 2 — Backend (`api/app.py`, `README.md`)

Satisfies: AC 1.1, AC 1.2, AC 1.3, AC 2.1, AC 2.2, AC 2.3, AC 2.4, AC 3.1, AC 3.2, AC 3.3, AC 3.4, AC 4.1, AC 4.2, AC 4.3, AC 4.4, AC 4.5, AC 4.6, AC 5.1, AC 5.2, AC 5.3, AC 5.4, AC 5.5

- [x] 2.1 `parse_due(value)` helper                                  → run: `/build-backend`
  - [x] 2.1.1 `value is None` → `(True, None)`
  - [x] 2.1.2 `value` not a `str`, or doesn't match `^\d{4}-\d{2}-\d{2}$`, or fails `datetime.date.fromisoformat` → `(False, None)` (AC 4.1–4.4, 4.6)
  - [x] 2.1.3 a well-formed, calendar-valid `"YYYY-MM-DD"` string → `(True, value)`
- [x] 2.2 `POST /tasks` validates and stores `due`                    → run: `/build-backend`
  - [x] 2.2.1 `"due" in body` and `parse_due` fails → `error(400, "due must be a valid date in YYYY-MM-DD form")`; `store.create` is never called (AC 4.1–4.4, no task created on rejection)
  - [x] 2.2.2 `"due" in body` and `parse_due` succeeds → `store.create(title, due=due)` (AC 1.1, 1.3)
  - [x] 2.2.3 `"due" not in body` → `store.create(title, due=None)` (AC 1.2)
- [x] 2.3 `PATCH /tasks/<id>` validates, updates, or clears `due`      → run: `/build-backend`
  - [x] 2.3.1 `"due" in body` and `parse_due` fails → `error(400, "due must be a valid date in YYYY-MM-DD form")`; `changes` is never populated with it and `store.update` is not called with an invalid value, so the task's stored `due` is unchanged (AC 4.5, 4.6)
  - [x] 2.3.2 `"due" in body` and `parse_due` succeeds → `changes["due"] = due`, including `due=None` to clear it (AC 3.1, 3.2)
  - [x] 2.3.3 `"due" not in body` → `changes` has no `due` key, so `store.update` leaves the stored `due` untouched (AC 3.3)
  - [x] 2.3.4 an unknown id still raises `NotFound` → `404 {"error": "no task with id <id>"}`, regardless of whether `due` in the body is present or valid (AC 3.4)
- [x] 2.4 `GET /tasks?overdue=true` filter and query-string routing   → run: `/build-backend`
  - [x] 2.4.1 `handle` splits the raw `path` into path and query (`urllib.parse.urlsplit`/`parse_qs`) once at the top, before the existing `if path == "/tasks":` / `TASK_PATH.match(path)` checks, so `/tasks/<id>` routing is unaffected
  - [x] 2.4.2 `handle(store, method, path, body=None, today=None)` gains a `today` parameter; when not given, defaults to `datetime.date.today()` (AGENTS.md: tests must not depend on today's date)
  - [x] 2.4.3 `GET /tasks` with `query.get("overdue") == ["true"]` returns only tasks where `due is not None and due < today.isoformat() and done is False` (AC 5.1, 5.2, 5.3, 5.4)
  - [x] 2.4.4 any other value of `overdue`, or no `overdue` key at all, returns `store.all()` unfiltered, same as before (AC 5.5)
- [x] 2.5 `README.md` endpoint table                                 → run: `/build-backend`
  - [x] 2.5.1 `POST /tasks` and `PATCH /tasks/<id>` rows mention `due`; add a row or note documenting `GET /tasks?overdue=true`, per `AGENTS.md`'s "update the endpoint table when the API changes"

### 2.X — Gate

> **CHECKER (Cat 1):** every check in `loop/2-backend-checker.md` returns its EXPECTED value.
> **CHECKER (Cat 2):** write `evidence/2-backend-gate.md` as a tick sheet.
> **CHECKER (Cat 3):** run `python3 -m unittest discover -s tests`; EXPECTED: all pass.

## Section 3 — Tests

Satisfies: every acceptance criterion and correctness property in `requirements.md`

- [x] 3.1 `tests/test_store.py` covers `TaskStore.create` with `due`    → run: `/build-tests`
  - [x] 3.1.1 `create(title)` with no `due` argument still returns a task with `"due": None` (back-compat)
  - [x] 3.1.2 `create(title, due="2026-11-01")` returns a task with that `due`
- [x] 3.2 `tests/test_app.py` covers every `due`-related acceptance criterion → run: `/build-tests`
  - [x] 3.2.1 `POST /tasks` with a valid `due`, with no `due` key, and with explicit `"due": null`, each returning `201` with the expected `due` (AC 1.1, 1.2, 1.3)
  - [x] 3.2.2 `due` is present on `GET /tasks`, `GET /tasks/<id>`, and `PATCH` responses, including for a task that never had `due` set (AC 2.1, 2.2, 2.3, 2.4)
  - [x] 3.2.3 `PATCH` sets a new `due`, clears it with `null`, and leaves it unchanged when `due` is omitted from the body; `PATCH` with a valid `due` on an unknown id still returns the standard `404` (AC 3.1, 3.2, 3.3, 3.4)
  - [x] 3.2.4 each invalid `due` (month 13, Feb 30, `"11/01/2026"`, non-string `20261101`, empty string `""`) returns `400` with `{"error": "due must be a valid date in YYYY-MM-DD form"}` and leaves stored state unchanged, on both `POST` and `PATCH` (AC 4.1, 4.2, 4.3, 4.4, 4.5, 4.6)
  - [x] 3.2.5 `GET /tasks?overdue=true`, with a fixed `today` passed into `handle`: a task due before `today` and not done is included; due exactly on `today` is excluded; due before `today` but done is excluded; `due: null` is excluded; `GET /tasks` with no `overdue` parameter still returns every task regardless of due date or done state (AC 5.1, 5.2, 5.3, 5.4, 5.5)
