#!/usr/bin/env python3
"""Check that a merge request followed the team's process. No AI involved.

    check_mr_process.py --repo CHECKOUT --base origin/main --config process.json \\
        --context issue_context.md --out report.md [--ok-file process.ok]

CHECKOUT is the merge request's branch. The config says where specs, code,
tests and migrations live, how strict each built-in check is, and holds the
team's own rules. The report is a markdown table of PASS, WARN and FAIL. The ok
file is written only when nothing failed, so a later stage can tell whether the
request has earned an agent's time.

The editor (factory/editor.py) reads CHECKS and RULE_TYPES below
and writes the config, so a check added here appears there.
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

# id, title, what it means in plain words, default level
CHECKS = [
    ("spec-before-code", "Spec before code", "Code changes come with a spec folder holding the required spec files.", "fail"),
    ("task-skills", "Every task names a skill", "Each task in tasks.md says which skill builds it, and that skill exists.", "fail"),
    ("evidence", "Ticked work has evidence", "A ticked section has its evidence file with a PASS status. Nothing is ticked as deferred.", "fail"),
    ("spec-checks", "Spec-adherence checks hold", "The script re-runs the checker commands in the spec and compares each with its expected value.", "fail"),
    ("traceability", "No unplanned code", "Changed code files are mentioned somewhere in the spec. Fails when none are; warns when some are not.", "fail"),
    ("tests", "Automated tests", "A layer's code changed, so a test file for that layer changed too.", "fail"),
    ("migrations", "Migrations handled safely", "No existing migration is edited, and every new one is registered in the changelog.", "fail"),
    ("secrets", "No secrets", "No tokens, keys, hard-coded credentials, or .env files are added.", "fail"),
    ("conflicts", "Merges cleanly", "The branch has no conflict with its target.", "fail"),
    ("linked-issue", "Linked to an issue", "The description names the issue the work is for.", "warn"),
    ("tasks-ticked", "All tasks ticked", "No task in the spec is left unticked.", "warn"),
    ("one-feature", "One feature per request", "The request touches a single spec folder.", "warn"),
    ("shared-config", "Shared configuration untouched", "Pipeline, standards and other protected paths are not changed.", "warn"),
    ("size", "Small enough to review", "The added code stays under the line limit.", "warn"),
]
DEFAULTS = {check[0]: check[3] for check in CHECKS}

# The kinds of rule a team can add for itself. `fields` drives the editor's form.
RULE_TYPES = {
    "forbid-pattern": {
        "sentence": "Lines added under {paths} must not match {pattern}",
        "fields": [("paths", "paths"), ("pattern", "pattern")],
    },
    "require-companion": {
        "sentence": "When files under {when} change, a file under {then} must change too",
        "fields": [("when", "paths"), ("then", "paths")],
    },
    "forbid-change": {
        "sentence": "Files under {paths} must not change",
        "fields": [("paths", "paths")],
    },
}

SECRETS = [
    (r"glpat-[A-Za-z0-9_\-]{20,}", "a GitLab token"),
    (r"gh[pous]_[A-Za-z0-9]{30,}", "a GitHub token"),
    (r"AKIA[0-9A-Z]{16}", "an AWS access key"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "a private key"),
    (r"(?i)\b(password|passwd|secret|api[_-]?key)\b\s*[:=]\s*[\"'][^\"'\s$<{]{8,}[\"']", "a hard-coded credential"),
]
COMMENT = ("//", "///", "*", "--", "#")


def git(repo, *args):
    return subprocess.run(["git"] + list(args), cwd=str(repo), text=True, capture_output=True).stdout


def under(path, prefixes):
    return any(path.startswith(p) for p in prefixes)


def names(paths, limit=5):
    return ", ".join("`{}`".format(Path(p).name) for p in paths[:limit]) + (" ..." if len(paths) > limit else "")


def validate(cfg):
    """Problems that would make a config unusable. An empty list means it is sound."""
    problems = []
    for key in ("spec_root", "code", "tests"):
        if not cfg.get(key):
            problems.append("`{}` is not set".format(key))
    for check, level in cfg.get("checks", {}).items():
        if check not in DEFAULTS:
            problems.append("unknown check `{}`".format(check))
        if level not in ("fail", "warn", "off"):
            problems.append("check `{}`: level must be fail, warn or off".format(check))
    for i, rule in enumerate(cfg.get("rules", [])):
        where = "rule {} ({})".format(i + 1, rule.get("name") or "unnamed")
        if rule.get("type") not in RULE_TYPES:
            problems.append("{}: unknown type".format(where))
            continue
        if not rule.get("name"):
            problems.append("{}: needs a name".format(where))
        if rule.get("level") not in ("fail", "warn", "off"):
            problems.append("{}: level must be fail, warn or off".format(where))
        for field, kind in RULE_TYPES[rule["type"]]["fields"]:
            if not rule.get(field):
                problems.append("{}: `{}` is empty".format(where, field))
            elif kind == "pattern" and rule.get("match") != "text":
                try:
                    re.compile(rule[field])
                except re.error as e:
                    problems.append("{}: the pattern is not valid ({})".format(where, e))
    return problems


def run(repo, base, cfg, context=""):
    """Returns rows of (result, title, detail) with result in PASS, WARN, FAIL."""
    repo = Path(repo)
    levels = dict(DEFAULTS, **cfg.get("checks", {}))
    rows = []

    def record(check, title, ok, detail="", soft=False):
        """soft: the check found something, but only enough for a warning."""
        level = levels.get(check, "fail")
        if level == "off":
            return
        result = "PASS" if ok else "WARN" if (soft or level == "warn") else "FAIL"
        rows.append((result, title, "" if ok and not detail else detail))

    status = {}
    for line in git(repo, "diff", "--name-status", base + "...HEAD").splitlines():
        parts = line.split("\t")
        status[parts[-1]] = parts[0][0]
    changed = sorted(status)
    added, path = {}, None
    for raw in git(repo, "diff", "-U0", base + "...HEAD").splitlines():
        if raw.startswith("+++ "):
            path = raw[6:] if raw.startswith("+++ b/") else None
        elif raw.startswith("+") and path and not raw.startswith("+++"):
            added.setdefault(path, []).append(raw[1:])

    code_all = [prefix for prefixes in cfg["code"].values() for prefix in prefixes]
    tests_all = [prefix for prefixes in cfg["tests"].values() for prefix in prefixes]
    is_test = lambda f: under(f, tests_all) or bool(re.search(cfg.get("test_file_pattern", r"(Tests?\.cs|\.spec\.tsx?|\.test\.tsx?)$"), f))
    code = [f for f in changed if under(f, code_all) and not is_test(f) and status[f] != "D"]
    spec_root = cfg["spec_root"].rstrip("/") + "/"
    spec_dirs = sorted({f[len(spec_root):].split("/")[0] for f in changed if f.startswith(spec_root) and "/" in f[len(spec_root):]})

    linked = bool(re.search(r"(#\d+|[A-Z][A-Z0-9]+-\d+)", context))
    record("linked-issue", "Linked to an issue", linked, "" if linked else "the description names no issue")

    spec = None
    if not code:
        record("spec-before-code", "Spec before code", True, "no application code changed")
    elif not spec_dirs:
        record("spec-before-code", "Spec before code", False,
               "{} code file(s) changed but nothing under `{}` was touched".format(len(code), spec_root))
    else:
        spec = repo / spec_root / spec_dirs[0]
        missing = [n for n in cfg.get("required_spec_files", ["requirements.md", "tasks.md"]) if not (spec / n).exists()]
        record("spec-before-code", "Spec before code", not missing,
               "`{}` has no {}".format(spec_dirs[0], " or ".join(missing)) if missing else "`{}`".format(spec_dirs[0]))
        if len(spec_dirs) > 1:
            record("one-feature", "One feature per request", False, "touches {} spec folders: {}".format(len(spec_dirs), ", ".join(spec_dirs)))

    tasks = spec / "tasks.md" if spec and (spec / "tasks.md").exists() else None
    if tasks:
        text = tasks.read_text()
        problems = lint_tasks.lint(text, [str(repo / d) for d in cfg.get("skills_dirs", [".claude/skills"])])
        record("task-skills", "Every task names a skill", not problems, "; ".join(problems[:4]) + (" ..." if len(problems) > 4 else ""))
        open_tasks = [t for s in lint_tasks.parse(text) if "outside the loop" not in s["title"]
                      for t, line in s["tasks"] if line.startswith("- [ ]")]
        record("tasks-ticked", "All tasks ticked", not open_tasks, "unticked: " + ", ".join(open_tasks[:8]) if open_tasks else "")
        problems = check_evidence.evidence_problems(spec)
        record("evidence", "Ticked work has evidence", not problems, "; ".join(problems[:3]))
        results, left = check_evidence.cat1(spec, repo)
        failed = [r for r in results if not r[4]]
        if results:
            record("spec-checks", "Spec-adherence checks hold", not failed,
                   "{} of {} re-run by script passed; {} left to a checker".format(len(results) - len(failed), len(results), len(left))
                   + ("; first mismatch: `{}` expected {}, got {}".format(failed[0][1][:60], failed[0][2], failed[0][3]) if failed else ""))
        spec_text = "\n".join(p.read_text(errors="ignore") for p in spec.rglob("*.md"))
        stray = [f for f in code if Path(f).stem not in spec_text and Path(f).name not in spec_text]
        if code:
            record("traceability", "No unplanned code", not stray,
                   "not mentioned in the spec: " + names(stray, 6) if stray else "", soft=len(stray) < len(code))

    for layer, prefixes in cfg["code"].items():
        touched = [f for f in code if under(f, prefixes)]
        if not touched or layer not in cfg["tests"]:
            continue
        tests = [f for f in changed if under(f, cfg["tests"][layer]) and status[f] != "D"]
        record("tests", "Automated tests for {} changes".format(layer), bool(tests),
               "{} test file(s) changed".format(len(tests)) if tests else "{} {} file(s) changed, no test file under {}".format(
                   len(touched), layer, " or ".join("`{}`".format(t) for t in cfg["tests"][layer])),
               soft=layer in cfg.get("tests_warn_only", []))

    migrations = cfg.get("migrations")
    if migrations and migrations.get("changes"):
        edited = [f for f in changed if f.startswith(migrations["changes"]) and status[f] == "M"]
        new = [f for f in changed if f.startswith(migrations["changes"]) and status[f] == "A"]
        log_path = repo / migrations.get("changelog", "")
        log = log_path.read_text() if migrations.get("changelog") and log_path.exists() else ""
        unregistered = [f for f in new if Path(f).name not in log]
        if edited or new:
            record("migrations", "Migrations handled safely", not edited and not unregistered,
                   "; ".join(x for x in ["edited: " + names(edited) if edited else "",
                                         "not in the changelog: " + names(unregistered) if unregistered else "",
                                         "{} new, registered".format(len(new)) if new and not unregistered and not edited else ""] if x))

    leaks = sorted({"{} in `{}`".format(what, Path(f).name) for f, lines in added.items() for line in lines
                    for pattern, what in SECRETS if re.search(pattern, line)})
    leaks += ["`{}` added".format(f) for f in changed if re.search(r"(^|/)\.env(\.|$)", f) and not f.endswith(".example") and status[f] != "D"]
    record("secrets", "No secrets", not leaks, "; ".join(leaks[:4]))

    guarded = [f for f in changed if under(f, cfg.get("protected", []))]
    if guarded:
        record("shared-config", "Shared configuration untouched", False, ", ".join("`{}`".format(f) for f in guarded[:5]))
    size, limit = sum(len(lines) for f, lines in added.items() if f in code), cfg.get("max_added_lines", 800)
    if size > limit:
        record("size", "Small enough to review", False, "{} lines of code added; the limit is {}".format(size, limit))
    if re.search(r"(?m)^- Conflicts with target: yes", context):
        record("conflicts", "Merges cleanly", False, "the branch conflicts with its target")

    # the team's own rules
    for rule in cfg.get("rules", []):
        level = rule.get("level", "fail")
        if level == "off":
            continue
        hits = []
        if rule["type"] == "forbid-pattern":
            # "text" rules are plain words typed by a person; only "regex" rules are patterns.
            pattern = "(?i)" + re.escape(rule["pattern"]) if rule.get("match") == "text" else rule["pattern"]
            hits = [f for f, lines in added.items() if under(f, rule["paths"]) and not is_test(f)
                    and any(re.search(pattern, line) for line in lines if not line.strip().startswith(COMMENT))]
        elif rule["type"] == "forbid-change":
            hits = [f for f in changed if under(f, rule["paths"])]
        elif rule["type"] == "require-companion":
            if any(under(f, rule["when"]) for f in changed) and not any(under(f, rule["then"]) and status[f] != "D" for f in changed):
                hits = [f for f in changed if under(f, rule["when"])]
        detail = names(hits) if hits else ""
        if hits and rule["type"] == "require-companion":
            detail = "changed {} but nothing under {}".format(names(hits, 3), " or ".join("`{}`".format(p) for p in rule["then"]))
        rows.append(("PASS" if not hits else "WARN" if level == "warn" else "FAIL", rule["name"], detail))
    return rows


def render(rows, base):
    fails, warns = sum(r[0] == "FAIL" for r in rows), sum(r[0] == "WARN" for r in rows)
    mark = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}
    verdict = "does not follow the process" if fails else "follows the process, with notes" if warns else "follows the process"
    report = ["## Process check: {}".format(verdict), "",
              "{} failed, {} to look at, {} passed. Checked by script against `{}`.".format(fails, warns, len(rows) - fails - warns, base),
              "", "| | Check | Detail |", "| --- | --- | --- |"]
    report += ["| {} | {} | {} |".format(mark[r], check, detail.replace("|", "\\|")) for r, check, detail in rows]
    if fails:
        report += ["", "The code was not reviewed. Fix the failed checks first, then the review runs on the next push."]
    return "\n".join(report) + "\n", fails, warns, verdict


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("repo", "base", "config", "out"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--context")
    p.add_argument("--ok-file")
    args = p.parse_args()
    cfg = json.loads(Path(args.config).read_text())
    problems = validate(cfg)
    if problems:
        sys.exit("check_mr_process: {} is not usable:\n- {}".format(args.config, "\n- ".join(problems)))
    context = Path(args.context).read_text() if args.context and Path(args.context).exists() else ""
    rows = run(args.repo, args.base, cfg, context)
    report, fails, warns, verdict = render(rows, args.base)
    Path(args.out).write_text(report)
    if args.ok_file:
        ok = Path(args.ok_file)
        if fails and ok.exists():
            ok.unlink()
        if not fails:
            ok.write_text("ok\n")
    print("{}: {} failed, {} warnings, {} passed".format(verdict, fails, warns, len(rows) - fails - warns))


if __name__ == "__main__":
    main()
