# Design: Tasks need a due date

## Data

`TaskStore` (`api/store.py:21-25`) gains a `due` field on the task dict, stored as either `None` or a `"YYYY-MM-DD"` string — never a `date` object, so `all()`/`get()`/`update()` keep returning plain JSON-serializable dicts unchanged.

- `TaskStore.create(title, due=None)` (`api/store.py:21`): task dict becomes `{"id": ..., "title": title, "done": False, "due": due}`. Default `due=None` means every existing call site that only passes `title` keeps working (covers "tasks created before this change keep working").
- `TaskStore.update(task_id, **changes)` (`api/store.py:27`): unchanged. `app.py` passes `due` in `changes` only when the caller supplied a valid value (including explicit `None` to clear), so a `PATCH` that omits `due` never touches the stored value (AC 3.3).
- No migration needed: `_tasks` is in-memory and only ever created through `create`, so no pre-existing task dict is missing the key at runtime.

## API / backend

All changes are in `api/app.py`; `store.py`'s contract (trusts its caller) is unchanged.

### Date validation — `validate_due(body, key="due")`

New helper, same shape as `validate_title`:

```
def parse_due(value):
    """Returns (ok, due) where due is a 'YYYY-MM-DD' str or None."""
    if value is None:
        return True, None
    if not isinstance(value, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return False, None
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        return False, None
    return True, value
```

- The regex pre-check rejects non-string/wrong-format input (AC 4.3 `"11/01/2026"`, AC 4.4 `20261101`, AC 4.6 `""`) before `fromisoformat` ever runs, so `fromisoformat`'s more lenient parsing (Python ≥3.11 accepts some non-`YYYY-MM-DD` ISO forms) never leaks through.
- `fromisoformat` raising `ValueError` catches calendar-invalid dates (AC 4.1 month 13, AC 4.2 Feb 30).
- Any failure returns the shared error `error(400, "due must be a valid date in YYYY-MM-DD form")` — one message for all four failure kinds, resolving "Needs clarification" in favor of simplicity, matching ACs 4.1–4.6 which all expect identical bodies.

### `POST /tasks` (`api/app.py:26-30`)

1. Validate `title` as today.
2. If `"due" in body`: call `parse_due(body["due"])`; on failure return `error(400, "due must be a valid date in YYYY-MM-DD form")` and do not call `store.create` (AC 4.1–4.4, no task created on rejection).
3. If `"due" not in body`: due is `None` (AC 1.2).
4. `store.create(title, due=due)` → `201`.

### `PATCH /tasks/<id>` (`api/app.py:39-46`)

Mirrors the existing `title`/`done` pattern:

```
if isinstance(body, dict) and "due" in body:
    ok, due = parse_due(body["due"])
    if not ok:
        return error(400, "due must be a valid date in YYYY-MM-DD form")
    changes["due"] = due
```

- Validation runs, and the 404 check (unknown id) and 400 check are independent of each other and of `title`/`done` validation, so an invalid `due` leaves the stored task (including `due`) untouched (AC 4.5, 4.6) — `changes["due"]` is only set after `parse_due` succeeds, and `store.update` is only called once at the end with whatever `changes` were accumulated, same as today.
- `due` omitted from the body → key absent from `changes` → `store.update` doesn't touch it (AC 3.3).
- `"due": null` in the body → `parse_due(None)` returns `(True, None)` → `changes["due"] = None`, clearing it (AC 3.2).
- Unknown id still raises `NotFound` → `404 {"error": "no task with id <id>"}`, same path as today (AC 3.4); this check is unaffected by whether `due` is present or valid.

### `GET /tasks` and `overdue=true` filter (`api/app.py:17-18`)

`handle`'s `path` argument is the raw HTTP path including any query string (`api/__main__.py:14` passes `self.path` straight through), but today's routing does `if path == "/tasks":` — an exact match that a query string breaks. Fix by splitting the query string off first:

```
from urllib.parse import urlsplit, parse_qs
...
split = urlsplit(path)
path, query = split.path, parse_qs(split.query)
```

applied once at the top of `handle`, before the existing `if path == "/tasks":` / `TASK_PATH.match(path)` checks — so `/tasks/<id>` routing is unaffected (no existing caller sends a query string there, and none is specified in this feature).

For `GET /tasks`:

- `query.get("overdue") == ["true"]` → filter: return only tasks where `due is not None and due < today_str and done is False` (AC 5.1–5.4). String comparison works because `due` is always `YYYY-MM-DD` (lexicographic order matches calendar order for fixed-width zero-padded ISO dates).
- Any other value, or no `overdue` key at all → return `store.all()` unfiltered, same as before (AC 5.5). This answers the second "Needs clarification" item: only the literal value `"true"` activates the filter; everything else (including `overdue=false` or `overdue=banana`) is treated as "no filter," consistent with `GET /tasks` never having validated query params before.

### "Today" for the overdue comparison

`AGENTS.md` requires tests not depend on the real date, so `handle` takes today's date as an optional parameter rather than calling `datetime.date.today()` unconditionally deep in the filter logic:

```
def handle(store, method, path, body=None, today=None):
    today = today or datetime.date.today()
    ...
    today_str = today.isoformat()
```

- Production caller (`api/__main__.py`) passes no `today`, so it defaults to the real current date — answers the first "Needs clarification" item: "today" is the server's local date (`datetime.date.today()`), not UTC, matching the only clock already available anywhere in this stdlib-only codebase.
- Tests pass a fixed `datetime.date(...)` (or `today="YYYY-MM-DD"` string, normalized with `datetime.date.fromisoformat` if given as a string) to get deterministic overdue results without patching the clock.

### Response shape

No separate change needed: since `store.create`/`store.update`/`all`/`get` always include `due` in the task dict (defaulting to `None`), every response already satisfies "every task has a `due` key, string or `null`, never absent" (Story 2's correctness property) for free — including tasks fetched by `GET /tasks/<id>`, `GET /tasks`, and `PATCH` responses (AC 2.1–2.4).

### README

Update the endpoint table (`README.md`) rows for `POST /tasks` and `PATCH /tasks/<id>` to mention `due`, and add a row/note for `GET /tasks?overdue=true`, per `AGENTS.md`'s "update the endpoint table when the API changes."

## Decisions

- **How "today" reaches the overdue filter**: add an optional `today` parameter to `handle`, defaulting to `datetime.date.today()`, over patching/mocking `datetime` in tests. Chosen because `AGENTS.md` explicitly says to pass the date in rather than depend on it; rejected the mocking approach since `handle`'s own signature is the natural seam and keeps `app.py` free of test-only hooks.
- **Shared vs. distinct error messages for invalid `due`** (resolves a "Needs clarification" item): one shared message for wrong type, wrong format, and invalid calendar date. Chosen because ACs 4.1–4.6 all specify the identical body; rejected per-case messages as unrequested extra surface area.
- **Non-`"true"` values of `?overdue=`** (resolves a "Needs clarification" item): treated as "no filter," same as omitting the parameter. Chosen for consistency with the API's existing lack of query-param validation anywhere else (e.g. unknown query keys are silently ignored too); rejected rejecting with `400` since AC 5.5 only pins down the no-parameter case and introducing new validation surface isn't asked for.
- **Timezone for "today"** (resolves a "Needs clarification" item): server local date via `datetime.date.today()`. Chosen as the only notion of "now" already reachable in this stdlib-only, single-process app; rejected UTC since nothing in the codebase currently distinguishes timezones.
- **String comparison vs. parsing to `date` for the overdue check**: compare `due` strings directly against `today.isoformat()` lexicographically. Chosen because fixed-width `YYYY-MM-DD` sorts identically to calendar order, avoiding a parse on every list call; rejected parsing each stored `due` back into a `date` object as unnecessary work given validation already guarantees the stored format.
