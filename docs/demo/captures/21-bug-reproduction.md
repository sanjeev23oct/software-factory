# Reproduction: trailing slash on /tasks/ gives 404

## Reported behavior
- `GET /tasks/` returns `404 {"error": "not found"}` instead of behaving like `GET /tasks`.
- Reporter says the same happens for `POST /tasks/` and for a single task, `GET /tasks/1/`.
- Reporter's own diagnosis ("API rejects it") is just a restatement of the symptom, not a cause — verified independently below.

## Steps to reproduce
1. `store = new_store()` (fresh in-memory store).
2. `handle(store, "GET", "/tasks/")` → `(404, {"error": "not found"})`, expected `(200, [])`.
3. `handle(store, "POST", "/tasks/", {"title": "a"})` → also 404 instead of creating a task.
4. `handle(store, "GET", "/tasks/1/")` → also 404 instead of fetching the created task.

## Failing test
Added to `tests/test_app.py`:

```python
def test_trailing_slash_is_treated_like_no_slash(self):
    self.assertEqual(self.call("GET", "/tasks/"), (200, []))
    status, task = self.call("POST", "/tasks/", {"title": "a"})
    self.assertEqual(status, 201)
    self.assertEqual(self.call("GET", "/tasks/1/"), (200, task))
```

Run: `python3 -m unittest discover -s tests -v`

Output (relevant excerpt):

```
test_trailing_slash_is_treated_like_no_slash (test_app.AppTest.test_trailing_slash_is_treated_like_no_slash) ... FAIL

======================================================================
FAIL: test_trailing_slash_is_treated_like_no_slash (test_app.AppTest.test_trailing_slash_is_treated_like_no_slash)
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../tests/test_app.py", line 40, in test_trailing_slash_is_treated_like_no_slash
    self.assertEqual(self.call("GET", "/tasks/"), (200, []))
AssertionError: Tuples differ: (404, {'error': 'not found'}) != (200, [])
```

All other existing tests still pass (9 passed, 1 new failure).

## Root cause
`api/app.py:23` compares the path with a strict equality `if path == "/tasks":`, and `api/app.py:7`'s `TASK_PATH = re.compile(r"^/tasks/(\d+)$")` has no allowance for a trailing slash either. Neither the collection route nor the single-item route strips or matches an optional trailing `/`, so any path with one falls through to the `error(404, "not found")` at `api/app.py:35`.

Confidence: high. No other code path normalizes the path before `handle` is called (confirmed by reading `api/__main__.py`'s thin wrapper and `api/app.py` in full), so this is the sole cause of the reported symptom for all three examples (`/tasks/`, `POST /tasks/`, `/tasks/1/`).

## Fix
Added a single normalization step at the top of `handle` (`api/app.py`): if `path` is not `"/"` and ends with `/`, strip the trailing slash before any route matching happens. This fixes the root cause (routes never accounted for a trailing `/`) once, for both the `/tasks` equality check and the `TASK_PATH` regex, rather than patching each route separately. `"/"` itself is left alone since stripping it would produce an empty string. No sibling code normalizes paths elsewhere (`api/__main__.py` passes the raw path straight through), so no other call site needed a matching change.
