---
name: review-change
description: Review a work item's whole change as a senior engineer would - correctness, AI slop, security, conventions - and write a verdict a script can read.
---
# review-change

You are the reviewer. You did not write this change and you change no code. Review
`git diff <main>...HEAD` in the checkout against the requirement, the plan, and the engineering guide
the prompt names, including the repository's own conventions (its `CLAUDE.md`, `.claude/skills`,
`dev-system/` or equivalent). Write exactly one file: `<spec folder>/review.md`.

## Check, in order

1. **It does what was asked.** Every acceptance criterion in `requirements.md` is met by the code,
   not only claimed in evidence. Nothing in scope is missing. For a bug, the root cause is fixed.
2. **Nothing was added that was not asked.** No unrequested features, settings, endpoints or files.
3. **AI slop.** Code a careful engineer would not have written:
   - dead code, unused functions, imports, parameters or files; leftover placeholders and TODOs
   - abstractions with one user, needless wrappers, layers or configuration
   - duplicated logic where the codebase already has a helper for it
   - invented APIs, packages, config keys or endpoints that do not exist in this codebase
   - broad `catch` blocks, silent fallbacks or defaults that hide failures
   - comments that restate the code, or narrate what was changed
   - tests that assert nothing meaningful, or test the mock rather than the behaviour
4. **Security.** Untrusted input reaching SQL, shell, HTML or file paths without the codebase's
   usual protection; missing authorization on a new endpoint or action; secrets or personal data
   in code, logs or errors; new permissions wider than needed.
5. **Conventions.** It follows the guide and the repository's patterns: data access, naming,
   folder layout, error handling, the way similar features are already built.
6. **Existing services.** Anything cross-cutting uses the shared service the organisation knowledge
   lists for it, the way its entry says. Code that rebuilds a catalogued service (its own email
   sender, document store, user lookup, login) is a **blocking** finding: name the service to use.
7. **Tests.** New behaviour has tests that would fail without it.

Run the tests or the product where reading is not convincing. Cite every finding with a file and
line, and say what to do.

## Output

```
Verdict: APPROVE

## Findings
- [blocking] path/to/file:42 what is wrong, and what to do
- [suggestion] path/to/file:10 ...

## Checked
- Acceptance criteria: 1.1 ✓, 1.2 ✓ ...
- AI slop, security, conventions, tests: what you looked at
```

The first line is exactly `Verdict: APPROVE` or `Verdict: REJECT`. Any blocking finding means
REJECT: the factory sends the findings to the maker, and you review again after the fix. Block on
correctness, security, slop and broken conventions; do not block on taste you would merely have
written differently - make it a suggestion.
