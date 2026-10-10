#!/usr/bin/env python3
"""Check that completed work is backed by evidence, without trusting the agent.

    check_evidence.py --spec path/to/spec-dir --repo path/to/checkout [--cat1]

  1. Every section of tasks.md whose tasks are ticked has its gate evidence
     file, and that file's status line says PASS.
  2. No box is ticked with a note that the check was skipped or deferred.
  3. With --cat1: re-run the Cat 1 checks in loop/*-checker.md and compare
     each result with its `# EXPECTED:` value. Only plain `grep` pipelines are
     run. Anything else is listed as left to the checker agent.

Exits 1 and lists every problem, or prints a summary ending in OK.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lint_tasks import EVIDENCE, parse  # noqa: E402

DEFERRED = re.compile(r"not written|deferred|apply on next run|skipped", re.I)
STATUS = re.compile(r"(Status|Verdict)\W*:.*", re.I)
EXPECTED = re.compile(r"#\s*EXPECTED:\s*(at least\s+)?(\d+)", re.I)
ASSIGN = re.compile(r"^[A-Z_][A-Z0-9_]*=[\w./\-\"']+$")
# One or more grep commands joined by pipes, with no redirection or substitution.
SAFE = re.compile(r"^grep\s[^;&<>`$()]*(\|\s*(grep\s[^;&<>`$()]*|wc -l\s*))*$")


def unquoted(command):
    """The command with every quoted string replaced by Q, so that shell
    syntax can be told apart from characters inside a grep pattern."""
    return re.sub(r"'[^']*'|\"[^\"`]*\"", "Q", command)


def evidence_problems(spec):
    problems, text = [], (spec / "tasks.md").read_text()
    for line in text.splitlines():
        if re.match(r"^\s*- \[[xX]\]", line) and DEFERRED.search(line):
            problems.append("ticked without being checked: {}".format(line.strip()[:110]))
    for section in parse(text):
        done = [t for t, line in section["tasks"] if re.match(r"- \[[xX]\]", line)]
        if not done:
            continue
        for rel in sorted(set(EVIDENCE.findall(section["gate"]))):
            path = spec / rel
            if not path.exists():
                problems.append('section "{}" has ticked tasks but {} does not exist'.format(section["title"][:40], rel))
                continue
            status = STATUS.search(path.read_text())
            if not status or "PASS" not in status.group(0):
                problems.append("{} does not record a PASS status".format(rel))
    return problems


def cat1(spec, repo):
    """Yields (checker file, command, expected, actual, ok) and unrunnable lines."""
    results, left = [], []
    for checker in sorted((spec / "loop").glob("*checker*.md")):
        env, pending = {}, None
        in_block = False
        for raw in checker.read_text().splitlines():
            line = raw.strip()
            if line.startswith("```"):
                in_block, pending = line == "```bash", None
                continue
            if not in_block or not line:
                continue
            command, _, comment = line.partition("#")
            command, expected = command.strip(), EXPECTED.search("#" + comment)
            if not command:
                if expected and pending:
                    results.append(run(checker.name, pending, expected, env, repo))
                    pending = None
                continue
            if ASSIGN.match(command):
                name, value = command.split("=", 1)
                env[name] = value.strip("\"'")
                continue
            if not SAFE.match(unquoted(command.replace("2>/dev/null", "")).strip()):
                left.append("{}: {}".format(checker.name, command[:90]))
                pending = None
            elif expected:
                results.append(run(checker.name, command, expected, env, repo))
                pending = None
            else:
                pending = command
    return results, left


def run(name, command, expected, env, repo):
    proc = subprocess.run(["sh", "-c", command], cwd=str(repo), env=dict(env, PATH="/usr/bin:/bin"),
                          text=True, capture_output=True)
    lines = proc.stdout.strip().splitlines()
    # `grep -c` prints the count. Any other grep is counted by its matching lines.
    counted = re.search(r"grep\s+(-\w*c\w*|--count)\b|wc -l", unquoted(command).split("|")[-1])
    actual = (lines[-1] if lines else "0") if counted else str(len(lines))
    want, at_least = int(expected.group(2)), bool(expected.group(1))
    ok = actual.isdigit() and (int(actual) >= want if at_least else int(actual) == want)
    return name, command, ("at least " if at_least else "") + str(want), actual, ok


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--spec", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--cat1", action="store_true")
    args = p.parse_args()
    spec, problems = Path(args.spec), []
    problems += evidence_problems(spec)
    if args.cat1:
        results, left = cat1(spec, Path(args.repo))
        failed = [r for r in results if not r[4]]
        print("Cat 1: {} checks run by script, {} passed, {} left to the checker agent".format(
            len(results), len(results) - len(failed), len(left)))
        for name, command, want, actual, _ in failed:
            problems.append("{}: expected {}, got {}: {}".format(name, want, actual, command[:90]))
    if problems:
        sys.exit("\n".join("- " + p for p in problems))
    print("OK")


if __name__ == "__main__":
    main()
