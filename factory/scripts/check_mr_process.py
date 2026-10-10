#!/usr/bin/env python3
"""Check that a merge request followed the team's process. No AI involved.

    check_mr_process.py --repo CHECKOUT --base origin/main --config process.json \\
        --context issue_context.md --out report.md [--ok-file process.ok]

CHECKOUT is the merge request's branch. The config says where specs, code,
tests and migrations live. The report is a markdown table of PASS, WARN and
FAIL. The ok file is written only when nothing failed, so a later stage can
tell whether the request has earned an agent's time.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import check_evidence  # noqa: E402
import lint_tasks  # noqa: E402

SECRETS = [
    (r"glpat-[A-Za-z0-9_\-]{20,}", "a GitLab token"),
    (r"gh[pous]_[A-Za-z0-9]{30,}", "a GitHub token"),
    (r"AKIA[0-9A-Z]{16}", "an AWS access key"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "a private key"),
    (r"(?i)\b(password|passwd|secret|api[_-]?key)\b\s*[:=]\s*[\"'][^\"'\s$<{]{8,}[\"']", "a hard-coded credential"),
]


def git(repo, *args):
    return subprocess.run(["git"] + list(args), cwd=str(repo), text=True, capture_output=True).stdout


def under(path, prefixes):
    return any(path.startswith(p) for p in prefixes)


def added_lines(repo, base):
    """{path: [added line, ...]} for the merge request."""
    lines, path = {}, None
    for raw in git(repo, "diff", "-U0", base + "...HEAD").splitlines():
        if raw.startswith("+++ "):
            path = raw[6:] if raw.startswith("+++ b/") else None
        elif raw.startswith("+") and path and not raw.startswith("+++"):
            lines.setdefault(path, []).append(raw[1:])
    return lines


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("repo", "base", "config", "out"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--context")
    p.add_argument("--ok-file")
    args = p.parse_args()
    repo, cfg = Path(args.repo), json.loads(Path(args.config).read_text())
    context = Path(args.context).read_text() if args.context and Path(args.context).exists() else ""

    status = {}
    for line in git(repo, "diff", "--name-status", args.base + "...HEAD").splitlines():
        parts = line.split("\t")
        status[parts[-1]] = parts[0][0]
    changed = sorted(status)
    added = added_lines(repo, args.base)
    code_all = [prefix for prefixes in cfg["code"].values() for prefix in prefixes]
    tests_all = [prefix for prefixes in cfg["tests"].values() for prefix in prefixes]
    is_test = lambda f: under(f, tests_all) or bool(re.search(cfg.get("test_file_pattern", r"(Tests?\.cs|\.spec\.tsx?|\.test\.tsx?)$"), f))
    code = [f for f in changed if under(f, code_all) and not is_test(f) and status[f] != "D"]
    spec_root = cfg["spec_root"].rstrip("/") + "/"
    spec_dirs = sorted({f[len(spec_root):].split("/")[0] for f in changed if f.startswith(spec_root) and "/" in f[len(spec_root):]})

    rows = []  # (result, check, detail)
    add = lambda result, check, detail="": rows.append((result, check, detail))

    # 1. the work is tied to an issue
    add("PASS" if re.search(r"(#\d+|[A-Z][A-Z0-9]+-\d+)", context) else "WARN", "Linked to an issue",
        "" if re.search(r"(#\d+|[A-Z][A-Z0-9]+-\d+)", context) else "the description names no issue")

    # 2-3. spec before code
    spec = None
    if not code:
        add("PASS", "Spec before code", "no application code changed")
    elif not spec_dirs:
        add("FAIL", "Spec before code", "{} code file(s) changed but nothing under `{}` was touched".format(len(code), spec_root))
    else:
        spec = repo / spec_root / spec_dirs[0]
        missing = [n for n in cfg.get("required_spec_files", ["requirements.md", "tasks.md"]) if not (spec / n).exists()]
        add("FAIL" if missing else "PASS", "Spec before code",
            "`{}` has no {}".format(spec_dirs[0], " or ".join(missing)) if missing else "`{}`".format(spec_dirs[0]))
        if len(spec_dirs) > 1:
            add("WARN", "One feature per request", "touches {} spec folders: {}".format(len(spec_dirs), ", ".join(spec_dirs)))

    tasks = spec / "tasks.md" if spec and (spec / "tasks.md").exists() else None
    if tasks:
        text = tasks.read_text()
        # 4. built by skills, not free-hand
        problems = lint_tasks.lint(text, [str(repo / d) for d in cfg.get("skills_dirs", [".claude/skills"])])
        add("FAIL" if problems else "PASS", "Every task names a skill", "; ".join(problems[:4]) + (" ..." if len(problems) > 4 else ""))
        # 5. finished
        open_tasks = [t for s in lint_tasks.parse(text) if "outside the loop" not in s["title"]
                      for t, line in s["tasks"] if line.startswith("- [ ]")]
        add("WARN" if open_tasks else "PASS", "All tasks ticked", "unticked: " + ", ".join(open_tasks[:8]) if open_tasks else "")
        # 6. proven
        problems = check_evidence.evidence_problems(spec)
        add("FAIL" if problems else "PASS", "Ticked work has PASS evidence", "; ".join(problems[:3]))
        results, left = check_evidence.cat1(spec, repo)
        failed = [r for r in results if not r[4]]
        if results:
            add("FAIL" if failed else "PASS", "Spec-adherence checks re-run",
                "{} of {} re-run by script passed; {} left to a checker".format(len(results) - len(failed), len(results), len(left))
                + ("; first mismatch: `{}` expected {}, got {}".format(failed[0][1][:60], failed[0][2], failed[0][3]) if failed else ""))
        # 7. no unplanned code
        spec_text = "\n".join(p.read_text(errors="ignore") for p in spec.rglob("*.md"))
        stray = [f for f in code if Path(f).stem not in spec_text and Path(f).name not in spec_text]
        if code:
            result = "PASS" if not stray else "FAIL" if len(stray) == len(code) else "WARN"
            add(result, "Every changed file is in the spec",
                "not mentioned in the spec: " + ", ".join("`{}`".format(Path(f).name) for f in stray[:6]) + (" ..." if len(stray) > 6 else "") if stray else "")

    # 8. automated tests
    for layer, prefixes in cfg["code"].items():
        touched = [f for f in code if under(f, prefixes)]
        if not touched or layer not in cfg["tests"]:
            continue
        tests = [f for f in changed if under(f, cfg["tests"][layer]) and status[f] != "D"]
        level = cfg.get("tests_required", {}).get(layer, "FAIL")
        add("PASS" if tests else level, "Automated tests for {} changes".format(layer),
            "{} test file(s) changed".format(len(tests)) if tests else "{} {} file(s) changed, no test file under {}".format(
                len(touched), layer, " or ".join("`{}`".format(t) for t in cfg["tests"][layer])))

    # 9. migrations
    migrations = cfg.get("migrations")
    if migrations:
        edited = [f for f in changed if f.startswith(migrations["changes"]) and status[f] == "M"]
        new = [f for f in changed if f.startswith(migrations["changes"]) and status[f] == "A"]
        if edited:
            add("FAIL", "Existing migrations untouched", "edited: " + ", ".join("`{}`".format(Path(f).name) for f in edited))
        if new:
            log = (repo / migrations["changelog"]).read_text() if (repo / migrations["changelog"]).exists() else ""
            unregistered = [f for f in new if Path(f).name not in log]
            add("FAIL" if unregistered else "PASS", "New migrations registered",
                "not in the changelog: " + ", ".join("`{}`".format(Path(f).name) for f in unregistered) if unregistered else "{} registered".format(len(new)))

    # 10. banned patterns from the standards
    for rule in cfg.get("banned", []):
        hits = [f for f, lines in added.items() if under(f, rule.get("paths", code_all)) and not is_test(f)
                and any(re.search(rule["pattern"], line) for line in lines if not line.strip().startswith(("//", "///", "*", "--", "#")))]
        if hits:
            add(rule.get("level", "FAIL"), "Standard: " + rule["why"], ", ".join("`{}`".format(Path(f).name) for f in hits[:5]))
    if cfg.get("banned") and not any(r[1].startswith("Standard: ") for r in rows):
        add("PASS", "No banned patterns from the standards")

    # 11. secrets
    leaks = sorted({"{} in `{}`".format(what, Path(f).name) for f, lines in added.items() for line in lines
                    for pattern, what in SECRETS if re.search(pattern, line)})
    leaks += ["`{}` added".format(f) for f in changed if re.search(r"(^|/)\.env(\.|$)", f) and not f.endswith(".example") and status[f] != "D"]
    add("FAIL" if leaks else "PASS", "No secrets", "; ".join(leaks[:4]))

    # 12-14. hygiene
    guarded = [f for f in changed if under(f, cfg.get("protected", []))]
    if guarded:
        add("WARN", "Shared configuration changed", ", ".join("`{}`".format(f) for f in guarded[:5]))
    size = sum(len(lines) for f, lines in added.items() if f in code)
    if size > cfg.get("max_added_lines", 800):
        add("WARN", "Small enough to review", "{} lines of code added".format(size))
    if re.search(r"(?m)^- Conflicts with target: yes", context):
        add("FAIL", "Merges cleanly", "the branch conflicts with its target")

    fails, warns = sum(r[0] == "FAIL" for r in rows), sum(r[0] == "WARN" for r in rows)
    mark = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}
    verdict = "does not follow the process" if fails else "follows the process, with notes" if warns else "follows the process"
    report = ["## Process check: {}".format(verdict), "",
              "{} failed, {} to look at, {} passed. Checked by script against `{}`.".format(
                  fails, warns, len(rows) - fails - warns, args.base), "",
              "| | Check | Detail |", "| --- | --- | --- |"]
    report += ["| {} | {} | {} |".format(mark[r], check, detail.replace("|", "\\|")) for r, check, detail in rows]
    if fails:
        report += ["", "The code was not reviewed. Fix the failed checks first, then the review runs on the next push."]
    Path(args.out).write_text("\n".join(report) + "\n")
    if args.ok_file:
        ok = Path(args.ok_file)
        if fails and ok.exists():
            ok.unlink()
        if not fails:
            ok.write_text("ok\n")
    print("{}: {} failed, {} warnings, {} passed".format(verdict, fails, warns, len(rows) - fails - warns))


if __name__ == "__main__":
    main()
