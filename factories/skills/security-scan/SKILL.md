---
name: security-scan
description: The mandatory security gate. A script, not a judgment - secrets, risky code and new vulnerable packages in what the change adds.
---
# security-scan

    python3 <factory>/factory/scripts/security_scan.py --repo <checkout> --base origin/<main> --report <spec folder>/evidence/security.md

Checks only what the change adds compared with the base branch, so findings that were already
there never block a request:

| Check | Tool | Blocks on |
|---|---|---|
| Secrets | gitleaks, over the commits since the base | any secret |
| Code | semgrep `p/default`, over the changed files | ERROR-severity findings |
| Packages | `dotnet list package --vulnerable`, `pnpm audit`, `npm audit`, when a manifest or lock file changed | a high or critical advisory the base does not have |

Exit 1 sends the findings to the maker, who fixes them; the checks run again after. Exit 2 means a
check could not run (a tool missing from the runner image): the item stops for a person, because a
gate that skips silently is no gate. The report is committed as evidence.

Every pipeline whose agents write code must have this stage; `flow.py validate` refuses one without it.
