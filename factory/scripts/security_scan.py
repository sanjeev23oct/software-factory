#!/usr/bin/env python3
"""The security gate: what this change adds, checked for secrets, risky code and vulnerable packages.

    security_scan.py --repo CHECKOUT --base origin/main [--report EVIDENCE.md]

Only the change is judged, so findings already on the base branch never block a request:

- secrets: gitleaks over the commits since the base
- code: semgrep's default rules over the files the change touched; ERROR findings block
- packages: when a manifest or lock file changed, the vulnerable packages (high or critical)
  on this branch that the base does not already have. dotnet for .NET, pnpm or npm for Node.

Exit 0 when the change is clean, 1 with the findings when it is not (the factory sends them to
the maker), and 2 when a check could not run, for example a tool missing from the image:
a security gate that silently skips is no gate.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DOTNET = re.compile(r"(\.csproj|\.sln|\.slnx|Directory\.Packages\.props|packages\.lock\.json)$")
NODE_LOCKS = ("pnpm-lock.yaml", "package-lock.json")


class CannotCheck(Exception):
    pass


def run(cmd, cwd, check_tool=True):
    if check_tool and not shutil.which(cmd[0]):
        raise CannotCheck("{} is not installed where the factory runs".format(cmd[0]))
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True)


def changed_files(repo, base):
    proc = run(["git", "diff", "--name-only", "--diff-filter=ACMR", "{}...HEAD".format(base)], repo)
    if proc.returncode:
        raise CannotCheck("cannot compare with {}: {}".format(base, proc.stderr.strip()[:300]))
    return [line for line in proc.stdout.splitlines() if line.strip()]


def secrets(repo, base):
    proc = run(["gitleaks", "detect", "--source", ".", "--log-opts", "{}..HEAD".format(base), "--no-banner",
                "--redact", "--report-format", "json", "--report-path", "/dev/stdout", "--exit-code", "3"], repo)
    if proc.returncode not in (0, 3):
        raise CannotCheck("gitleaks failed: " + (proc.stderr or proc.stdout).strip()[:300])
    found = json.loads(proc.stdout or "[]") if proc.returncode == 3 else []
    return ["secret ({}) in {}:{}".format(f.get("RuleID"), f.get("File"), f.get("StartLine")) for f in found]


def code(repo, files):
    files = [f for f in files if (repo / f).is_file()]
    if not files:
        return []
    proc = run(["semgrep", "scan", "--config", "p/default", "--severity", "ERROR", "--metrics", "off",
                "--json", "--quiet"] + files, repo)
    if proc.returncode not in (0, 1):
        raise CannotCheck("semgrep failed: " + (proc.stderr or proc.stdout).strip()[:300])
    results = json.loads(proc.stdout or "{}").get("results", [])
    return ["{} at {}:{}: {}".format(r["check_id"].split(".")[-1], r["path"], r["start"]["line"],
                                     " ".join(r["extra"].get("message", "").split())[:200]) for r in results]


def vulnerable(repo, files):
    """{(ecosystem, package, version, advisory)} for high and critical advisories in this tree."""
    found = set()
    if any(DOTNET.search(f) for f in files):
        targets = sorted(p for p in repo.rglob("*.sln*") if "node_modules" not in p.parts) or \
            sorted(p for p in repo.rglob("*.csproj") if "node_modules" not in p.parts)
        for target in targets:
            restore = run(["dotnet", "restore", str(target), "--nologo", "-v", "q"], repo)
            if restore.returncode:
                raise CannotCheck("dotnet restore failed for {}: {}".format(target.name, restore.stdout[-300:]))
            proc = run(["dotnet", "list", str(target), "package", "--vulnerable", "--include-transitive",
                        "--format", "json"], repo)
            if proc.returncode:
                raise CannotCheck("dotnet list package failed: " + (proc.stderr or proc.stdout)[-300:])
            for project in json.loads(proc.stdout).get("projects", []):
                for framework in project.get("frameworks", []):
                    for package in framework.get("topLevelPackages", []) + framework.get("transitivePackages", []):
                        for advisory in package.get("vulnerabilities", []):
                            if advisory.get("severity", "").lower() in ("high", "critical"):
                                found.add(("nuget", package["id"], package.get("resolvedVersion", ""),
                                           advisory.get("advisoryurl", "")))
    for lock in NODE_LOCKS:
        for path in sorted(p for p in repo.rglob(lock) if "node_modules" not in p.parts):
            if not any(f.endswith(lock) for f in files):
                continue
            tool = "pnpm" if lock.startswith("pnpm") else "npm"
            proc = run([tool, "audit", "--json", "--audit-level", "high"], path.parent)
            try:
                report = json.loads(proc.stdout or "{}")
            except ValueError:
                raise CannotCheck("{} audit gave no report: {}".format(tool, (proc.stderr or proc.stdout)[-300:]))
            for advisory in (report.get("advisories") or {}).values():           # pnpm
                if advisory.get("severity") in ("high", "critical"):
                    found.add(("npm", advisory.get("module_name"), "", advisory.get("url", "")))
            for name, entry in (report.get("vulnerabilities") or {}).items():    # npm
                if entry.get("severity") in ("high", "critical"):
                    found.add(("npm", name, entry.get("range", ""), ""))
    return found


def packages(repo, base, files):
    if not any(DOTNET.search(f) or f.endswith(NODE_LOCKS) for f in files):
        return []
    with tempfile.TemporaryDirectory() as tmp:
        before = Path(tmp) / "base"
        if run(["git", "worktree", "add", "-q", "--detach", str(before), base], repo).returncode:
            raise CannotCheck("cannot check out {} to compare packages".format(base))
        try:
            new = vulnerable(repo, files) - vulnerable(before, files)
        finally:
            run(["git", "worktree", "remove", "--force", str(before)], repo)
    return ["vulnerable package {} {} {} {}".format(e, name, version, url).strip() for e, name, version, url in sorted(new)]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--report")
    args = parser.parse_args()
    repo = Path(args.repo)
    rows, findings = [], []
    try:
        files = changed_files(repo, args.base)
        for name, check in (("Secrets (gitleaks, commits since {})".format(args.base), lambda: secrets(repo, args.base)),
                            ("Code (semgrep p/default, {} changed files)".format(len(files)), lambda: code(repo, files)),
                            ("New vulnerable packages (high, critical)", lambda: packages(repo, args.base, files))):
            found = check()
            rows.append((name, "PASS" if not found else "FAIL", len(found)))
            findings += found
    except CannotCheck as e:
        print("security: could not check: {}".format(e))
        sys.exit(2)
    status = "FAIL" if findings else "PASS"
    report = ["Status: {}".format(status), "", "# Security check", "",
              "Only what this change adds, compared with `{}`.".format(args.base), "",
              "| Check | Result | Findings |", "| --- | --- | --- |"]
    report += ["| {} | {} | {} |".format(*row) for row in rows]
    report += ["", "## Findings", ""] + ["- " + f for f in findings] if findings else []
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text("\n".join(report) + "\n")
    print("\n".join(report))
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
