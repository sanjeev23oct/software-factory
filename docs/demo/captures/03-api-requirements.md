# Requirements: Tasks need a due date

## Overview

The API currently has no way to attach a deadline to a task: `TaskStore.create` only stores `title` and `done` (`api/store.py:21-25`), and `app.py` only validates `title` and `done` on create/update (`api/app.py:14-50`). Tasks returned by the API always carry the same fields (per `AGENTS.md`), so every task response today is exactly `{"id", "title", "done"}`. This feature adds an optional `due` date to a task: settable on create, changeable or clearable on an existing task, rejected when not a real calendar date, and filterable via `GET /tasks?overdue=true`.

## User stories

### Story 1: Set a due date when creating a task

As a person tracking work with deadlines,
I want to send a due date when I create a task,
So that the deadline is recorded with the task instead of buried in its title.

- AC 1.1: `POST /tasks` with body `{"title": "Renew the domain", "due": "2026-11-01"}` returns `201` and a task with `"due": "2026-11-01"`.
- AC 1.2: `POST /tasks` with body `{"title": "Renew the domain"}` (no `due` key) returns `201` and a task with `"due": null`.
- AC 1.3: `POST /tasks` with `"due": null` returns `201` and a task with `"due": null`.

### Story 2: Due date comes back wherever a task is returned

As a person tracking work with deadlines,
I want the due date included on every task I get back from the API,
So that I don't have to look it up separately.

- AC 2.1: `GET /tasks/<id>` includes the `due` field with the value last set for that task (or `null`).
- AC 2.2: `GET /tasks` returns a list where every task includes the `due` field.
- AC 2.3: `PATCH /tasks/<id>` returns the updated task including the `due` field, whether or not `due` was part of this patch.
- AC 2.4: A task created before this feature existed (no `due` ever set) is returned with `"due": null`.

### Story 3: Change or clear a due date on an existing task

As a person tracking work with deadlines,
I want to change or remove a task's due date after creating it,
So that I can adjust a deadline that moved or no longer applies.

- AC 3.1: `PATCH /tasks/<id>` with `{"due": "2026-12-25"}` returns `200` and the task's `due` is now `"2026-12-25"`.
- AC 3.2: `PATCH /tasks/<id>` with `{"due": null}` returns `200` and the task's `due` is now `null`.
- AC 3.3: `PATCH /tasks/<id>` that omits `due` entirely leaves the task's existing `due` unchanged.
- AC 3.4: `PATCH /tasks/<id>` with `{"due": "2026-12-25"}` for an id that does not exist returns `404` with body `{"error": "no task with id <id>"}`, same as any other `PATCH` on an unknown id.

### Story 4: Invalid due dates are rejected

As a person tracking work with deadlines,
I want a due date that isn't a real calendar date to be refused,
So that bad data never silently lands on a task.

- AC 4.1: `POST /tasks` with `{"title": "a", "due": "2026-13-01"}` (month 13 does not exist) returns `400` with body `{"error": "due must be a valid date in YYYY-MM-DD form"}`, and no task is created.
- AC 4.2: `POST /tasks` with `{"title": "a", "due": "2026-02-30"}` (February has no 30th day) returns `400` with the same error body, and no task is created.
- AC 4.3: `POST /tasks` with `{"title": "a", "due": "11/01/2026"}` (wrong format) returns `400` with the same error body, and no task is created.
- AC 4.4: `POST /tasks` with `{"title": "a", "due": 20261101}` (not a string) returns `400` with the same error body, and no task is created.
- AC 4.5: `PATCH /tasks/<id>` with `{"due": "2026-13-01"}` returns `400` with the same error body, and the task's stored `due` is unchanged.
- AC 4.6: `PATCH /tasks/<id>` with `{"due": ""}` returns `400` with the same error body, and the task's stored `due` is unchanged.

### Story 5: Find overdue tasks

As a person tracking work with deadlines,
I want to list only the tasks that are late,
So that I can see what needs attention without scanning every task.

- AC 5.1: `GET /tasks?overdue=true` returns `200` and only the tasks whose `due` is strictly before today's date and whose `done` is `false`.
- AC 5.2: A task whose `due` equals today's date is not included in the `overdue=true` result (not overdue yet).
- AC 5.3: A task whose `due` is before today's date but whose `done` is `true` is not included in the `overdue=true` result.
- AC 5.4: A task with `due` of `null` is never included in the `overdue=true` result.
- AC 5.5: `GET /tasks` (no `overdue` parameter) returns all tasks regardless of due date or done state, same as before this feature.

## Correctness properties

- Every task returned by the API — from `POST`, `GET /tasks`, `GET /tasks/<id>`, or `PATCH` — has a `due` key, with value either a `"YYYY-MM-DD"` string or `null`. Never absent, never any other type.
- A `due` value that reaches storage is always either `null` or a string that denotes a real calendar date in `YYYY-MM-DD` form. No partially-validated or malformed date is ever persisted, even transiently.
- A rejected `due` (create or update) never changes stored state: on `POST`, no task is created; on `PATCH`, the task's existing `due` (and all other fields) stay exactly as they were.
- "Overdue" is evaluated against the date at the time of the request, not a fixed date baked into a task.
- All pre-existing behavior for `title` and `done` (validation rules, error messages, status codes) is unchanged by this feature.

## Out of scope

- Due times (hours/minutes) — only a calendar date, not a timestamp.
- Timezone handling for "today" — this spec does not define which timezone's "today" is used beyond what's raised in "Needs clarification" below.
- Sorting or filtering by due date other than the `overdue=true` filter (e.g. `before=`, `after=`, sort order).
- Notifications or reminders about approaching or passed due dates.

## Needs clarification

- Which clock/timezone defines "today" for the `overdue` comparison (e.g. server's local date vs. UTC)? The issue just says "before today."
- Does `GET /tasks?overdue=false` (or any value other than `true`) behave like `GET /tasks` (all tasks), get rejected as a bad request, or return only non-overdue tasks? The issue only specifies `overdue=true`.
- Should the due-date validation error message distinguish between "wrong type," "wrong format," and "not a real date," or is one shared message (as assumed in AC 4.1–4.6) sufficient?
