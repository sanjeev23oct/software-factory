---
title: Rename a task
author: sam
state: open
labels: agent:feature, area:cli, triaged, ready-to-spec, spec-reviewed
---
If I make a typo in a task title the only fix is to rm it and add it again, which gives it a new id and loses the done state. I would like to change the title of an existing task in place.

---
**factory-triage** · 2026-10-09 02:30 UTC

Type: feature. This asks for a new capability (change a task's title in place), not a fix for wrong behavior.

**Confirmed the limitation** on a scratch `--db` file (no real data touched):

    add "tpyo"      -> added 1
    done 1          -> done 1
    rename 1 typo   -> exit 2, argparse: invalid choice: 'rename' (choose from 'add', 'list', 'done', 'rm')
    rm 1; add typo  -> list shows "[ ]   2  typo"

So the only workaround today does lose both the id and the done state, exactly as reported.

**Where it touches the code**
- `tasklite/cli.py:14-23` - the subparsers are `add`, `list`, `done`, `rm`; a new subcommand taking an id and a new title is needed here.
- `tasklite/cli.py:37-55` - command dispatch; the new branch should reuse the existing `TaskNotFound` -> `error: no task with id N` / exit 1 path (`tasklite/cli.py:53-55`).
- `tasklite/store.py:26-44` - `Store` has `add`, `complete`, `remove` and no title mutator. A new method can follow `complete` (`tasklite/store.py:38-41`): look the task up with `_find_index` and set `task["title"]`, leaving `id` and `done` untouched.
- `tasklite/store.py:27-28` - why the workaround loses state: `add` always takes a fresh `next_id` and sets `done` to `False`.
- No change to the task file format is needed: only the existing `title` field is rewritten, so old task files keep loading.
- Tests in `tests/test_store.py` and `tests/test_cli.py`, plus the README command list.

**Duplicate check:** not a duplicate. GH1 (`done` index bug, closed), GH2 (due dates), GH3 (vague no-repro), GH4 (sync) and GH5 (traceback on empty task file) describe different problems; none requests editing a title.

**No follow-up questions.** The need is clear and nothing is missing that only the reporter could supply.

**Recommendation: `ready-to-spec`.** The implementation is small, but the user-visible choices are open and should be settled first: the command name (`rename` vs `edit` vs `mv`), the success output text (e.g. `renamed 1`), and what happens with an empty or whitespace-only new title (note `add` currently accepts an empty title, so the spec should decide whether rename matches that or rejects it). If the maintainer is happy to pick `rename <id> <title>` printing `renamed <id>` directly, this could go straight to `ready-to-implement`.

Readiness recommendation for the maintainer: `ready-to-spec`

---
**maintainer** · 2026-10-09 02:30 UTC

Applied label `ready-to-spec`.

---
**factory-spec** · 2026-10-09 02:41 UTC

Related issue: GH6

Adds `specs/GH6/product.md` and `specs/GH6/tech.md` for a new `rename` command.

**Product spec.** `tasklite rename <id> <title>` changes a task's title in place and prints `renamed <id>`. The task keeps its id, done state and list position, and no id is consumed. The title is stored verbatim as a single argument. An unknown id gives the existing `error: no task with id <id>` on stderr with exit 1 and leaves the task file untouched. Usage errors behave as for the existing commands (exit 2). The task file format does not change.

**Tech spec.** One new `Store.rename(task_id, title)` method beside `complete`, one new subparser and one dispatch branch in `cli.py` reusing the shared `TaskNotFound` path. Lists the store and CLI test cases that prove each invariant. No README change: the README has no tasklite command list.

**Open questions for the maintainer**

1. Command name: the spec picks `rename` (the reporter's word). `edit` and `mv` were the alternatives raised in triage.
2. Empty or whitespace-only title: the spec accepts it and stores it as given, matching what `add` does today. The alternative is to reject it, either in `rename` only (the two commands would then disagree) or in both (wider than this issue).

**Note.** The unmerged `factory/GH5` branch edits the same `try`/`except` block in `cli.py`, so the implementation may hit a small textual conflict depending on merge order.

Specs: `specs/GH6/` on branch `factory/GH6`

---
**factory-review** · 2026-10-09 02:55 UTC

**Spec review round 1: request changes**

## Overview
The specs cover the whole issue: `rename <id> <title>` changes the title in place and keeps id, done state, list position and `next_id`. The plan is feasible and matches the code it cites at `c5b1351` (`tasklite/cli.py:12-23`, `:37-55`, `tasklite/store.py:22-41`). It respects AGENTS.md: mutation stays in `store.py`, the file format is untouched, the error path is the shared `error: no task with id N` / exit 1, and nothing outside the standard library is needed. Scope matches the issue, and the README claim is correct (it has no tasklite command list).

I checked the stated behavior against the existing CLI on a scratch `--db` file and against a copy of the proposed subparser on Python 3.9.6, 3.13 and 3.14. Confirmed as written: invariants 1, 6, 7, 10, 11 (including `0` and `-1`), 12 (no file created on failure), 13 (all four usage cases exit 2) and 16, plus the exact `list` strings in invariants 6 and 10. Every invariant maps to a test or to a stated coverage argument.

The two open questions (command name, empty title) are maintainer decisions and are not counted as defects.

## Concerns
- Invariant 14 is wrong as a general rule. Only some titles beginning with `-` need `--`. `-1`, `-3.5`, `- buy milk` and `-x y` are accepted without it, today by `add` and by the proposed `rename` parser. As written, the invariant requires a usage error that the tech spec's plain-argparse plan will not produce, so the two specs contradict each other. The tech spec Context repeats the same claim.
- A title of exactly `--` is not covered, and on Python 3.9 (the version AGENTS.md requires) `rename 1 -- --` yields a list `[]` as the title, which would be written to the task file. On 3.13 and 3.14 it yields the string `--`.
- Invariant 13 promises a usage message on stderr, but the planned test asserts only the exit code.

## Verdict
Found: 0 critical, 1 important, 2 suggestions

**Request changes**

`specs/GH6/product.md:53` ⚠️ [IMPORTANT] This invariant is false as a general rule, and contradicts the tech spec. Argparse only treats a `-` argument as an option when it has no space and is not number-like. Verified on Python 3.9.6, 3.13 and 3.14 with the proposed subparser, and with today's `add`: `rename 1 -1` sets the title to `-1`, `rename 1 -3.5` to `-3.5`, `rename 1 "- buy milk"` to `- buy milk`, and `rename 1 "-x y"` to `-x y`, all exit 0 without `--`. Only titles like `-x` or `--foo` fail with exit 2. An implementer holding to "without `--` it is a usage error" would have to add title validation that the tech spec explicitly rules out ("does not validate or normalise `title`"). Narrow the invariant to what ships, for example: "A title the argument parser would read as an option (such as `-x` or `--foo`) must be passed after `--`, the same as for `add`: `rename 1 -- -x` sets the title to `-x`, and `rename 1 -x` is a usage error under invariant 13. Other titles beginning with `-`, such as `-1` or `"- buy milk"`, are accepted without `--` and stored verbatim." Make the same correction in `tech.md` Context (lines 9-11, "already requires `--` before a title starting with `-`"), and add one accepted case such as `rename 1 -1` to `test_rename_title_starting_with_dash` so the boundary is pinned.

`specs/GH6/tech.md:88` 💡 [SUGGESTION] Decide and state what a title of exactly `--` does. With the proposed two-positional subparser, `rename 1 -- --` parses to `title == []` (a list, not a string) on Python 3.9.6, and to `'--'` on 3.13 and 3.14. AGENTS.md requires Python 3.9, so on the supported floor the plan would write a non-string title into the task file and `list` would print `[]`, which breaks invariant 6 ("stored exactly as given"). `add -- --` does not have this problem on 3.9 because it has a single positional. Either add a product invariant plus a test for this input (and have the CLI branch reject or normalise a non-string title before calling `store.rename`), or record it under Risks as a known, accepted argparse limitation on 3.9.

`specs/GH6/tech.md:84` 💡 [SUGGESTION] Invariant 13 promises "a usage message on stderr", but this test only asserts the exit code. Since stderr is already captured with `contextlib.redirect_stderr`, also assert the captured text contains `usage:` for each case, so the whole invariant is proven. Note that for `rename 1 a b` the usage line comes from the top-level parser (`tasklite: error: unrecognized arguments: b`), not the `rename` subparser, so assert on `usage:` rather than on `tasklite rename`.

---
**factory-spec** · 2026-10-09 02:56 UTC

Related issue: GH6

Revises `specs/GH6/product.md` and `specs/GH6/tech.md` for the `rename` command after spec review round 1.

**Product spec.** `tasklite rename <id> <title>` changes a task's title in place and prints `renamed <id>`. The task keeps its id, done state and list position, and no id is consumed. The title is a single argument stored verbatim. An unknown id gives the existing `error: no task with id <id>` on stderr with exit 1 and leaves the task file untouched. Usage errors exit 2 with a usage message. The task file format does not change.

**Tech spec.** One new `Store.rename(task_id, title)` method beside `complete`, one new subparser and one dispatch branch in `cli.py` reusing the shared `TaskNotFound` path. Every invariant maps to a named test.

**Changes in this round**

- Invariant 14 narrowed to what argparse does: only option-like titles (`-x`, `--foo`) need `--`. `-1`, `-3.5`, `"- buy milk"`, `"-x y"` and `-` are accepted without it. The tech spec Context is corrected the same way and the dash test now pins the accepted cases.
- New invariant 15: `rename 1 -- --` sets the title to `--` on every supported Python version, matching `add -- --`. On Python 3.9 argparse returns `[]` for this input, so the CLI branch substitutes `"--"` for a non-string title. A dedicated test checks the stored value is a string; it only proves the fix when run on 3.9.
- New invariant 16: `rename 1 -h` prints the `rename` help and exits 0 without changing anything.
- The usage-error test now asserts stderr contains `usage:` as well as exit code 2.
- Later invariants are renumbered (old 15-18 are now 17-20).

**Open questions for the maintainer**

1. Command name: the spec picks `rename` (the reporter's word). `edit` and `mv` were the alternatives raised in triage.
2. Empty or whitespace-only title: the spec accepts it and stores it as given, matching what `add` does today. The alternative is to reject it, either in `rename` only (the two commands would then disagree) or in both (wider than this issue).

**Note.** The unmerged `factory/GH5` branch edits the same `try`/`except` block in `cli.py`, so the implementation may hit a small textual conflict depending on merge order.

Specs: `specs/GH6/` on branch `factory/GH6`

---
**factory-review** · 2026-10-09 02:58 UTC

**Spec review round 2: approve**

## Overview
Round 2. All three round 1 findings are resolved: invariant 14 is narrowed to what argparse does, a title of exactly `--` has its own invariant (15), a planned fix and a test, and the usage-error test now asserts `usage:` on stderr.

The specs cover the whole issue: `rename <id> <title>` changes the title in place and keeps id, done state, list position and `next_id`. Scope matches the issue. The plan respects AGENTS.md: mutation stays in `store.py`, the file format is untouched, the error path is the shared `error: no task with id N` / exit 1, and only the standard library is used. The code citations (`tasklite/cli.py:12-23`, `:37-55`, `tasklite/store.py:22-30`, `:32-41`) match the checkout, the README has no tasklite command list, and `factory/GH5` exists unmerged as the Risks section says.

I rebuilt the proposed subparser and ran it on Python 3.9.6, 3.13.13 and 3.14.6. Confirmed as written on all three: every example in invariants 13, 14 and 16 (exit codes, `usage:` on stderr, `usage: tasklite rename` on stdout for `-h`), `rename -1 x` and `rename 0 x` reaching the not-found path (invariant 11), and `rename 1 --` being a usage error. Confirmed for invariant 15: `rename 1 -- --` gives `title == []` on 3.9.6 and `'--'` on 3.13 and 3.14, and `[]` appeared for no other input I tried, so the planned "non-string means `--`" substitution is sound. Every invariant maps to a named test or a stated coverage argument, and the invariant numbers in `tech.md` agree with `product.md` after the renumbering.

The two open questions (command name, empty title) are maintainer decisions and are not counted as defects.

## Concerns
- Whether `test_rename_title_double_dash` proves the `--` fix depends on which Python runs `./script/presubmit`. It can be made to fail without the fix on every version.
- Invariant 14's sentence "Other titles beginning with `-` are accepted without `--`" is slightly broader than argparse: `rename 1 -1x` is a usage error on 3.9.6 and 3.13 and is accepted on 3.14. The listed examples are all correct.

Neither blocks implementation.

## Verdict
Found: 0 critical, 0 important, 2 suggestions

**Approve with nits**

`specs/GH6/tech.md:120` 💡 [SUGGESTION] Make this proof independent of the interpreter. As the spec says at lines 138-140, this test passes on 3.13+ without the `--` handling, so the invariant 15 fix is only proven where `python3` happens to be 3.9 (`script/presubmit` calls plain `python3`). Add a second case that feeds the branch the 3.9 parse result directly, for example with `unittest.mock.patch` on `tasklite.cli.build_parser` returning a parser whose `parse_args` yields `argparse.Namespace(db=self.db, command="rename", id=1, title=[])`, and assert the stored title is the `str` `"--"`. That test fails without the fix on every version, which is what AGENTS.md asks of a test for new behavior, and the manual 3.9 run becomes a cross-check instead of the only proof.

`specs/GH6/product.md:56` 💡 [SUGGESTION] "Other titles beginning with `-` are accepted without `--`" is broader than what ships. With the proposed subparser, `rename 1 -1x` exits 2 on Python 3.9.6 and 3.13.13 and sets the title to `-1x` on 3.14.6, so the sentence is false for that input on the supported floor. The five listed examples are all correct on all three versions. Scope the sentence to them, for example: "A title beginning with `-` that is a number, contains a space, or is `-` alone is accepted without `--` and stored verbatim: ...". Add one line saying that for any other title beginning with `-`, `--` is the form that always works. Do not add a test for `-1x`, since its result differs by Python version.
