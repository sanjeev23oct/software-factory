#!/usr/bin/env python3
"""Check that a tasks.md is fit to be built by the maker-checker loop.

    lint_tasks.py path/to/tasks.md --skills-dir path/to/.claude/skills

Rules:
  1. Every task (a checkbox numbered N.M) names a skill: `→ run: `/skill``.
  2. Every named skill exists in the skills directory.
  3. Every section that has tasks ends in a gate with checker categories
     Cat 1, Cat 2 and Cat 3. Sections marked "outside the loop" and the Tests
     section are exempt.
  4. Every gate names the evidence file its checker writes.

Exits 1 and lists every violation, or prints OK.
"""

import argparse
import re
import sys
from pathlib import Path

TASK = re.compile(r"^- \[[ xX]\] (\d+\.\d+) (.*)$")
RUN = re.compile(r"run:\s*`/([\w-]+)`")
SECTION = re.compile(r"^## (.+)$")
EVIDENCE = re.compile(r"evidence/[\w.\-]+\.md")


def parse(text):
    """Returns sections as dicts: title, tasks [(id, line)], gate text."""
    sections, current, in_gate = [], None, False
    for line in text.splitlines():
        heading = SECTION.match(line)
        if heading:
            current = {"title": heading.group(1).strip(), "tasks": [], "gate": ""}
            sections.append(current)
            in_gate = False
        elif current is None:
            continue
        elif re.match(r"^#{3,4} .*Gate", line):
            in_gate = True
        elif re.match(r"^#{3,4} ", line):
            in_gate = False
        elif in_gate:
            current["gate"] += line + "\n"
        else:
            task = TASK.match(line)
            if task:
                current["tasks"].append((task.group(1), line))
    return [s for s in sections if s["tasks"]]


def lint(text, skills_dirs):
    errors = []
    for section in parse(text):
        where = 'section "{}"'.format(section["title"][:50])
        for task_id, line in section["tasks"]:
            skill = RUN.search(line)
            if not skill:
                errors.append("task {} names no skill (expected: → run: `/skill`)".format(task_id))
            elif skills_dirs and not any((Path(d) / skill.group(1) / "SKILL.md").exists() for d in skills_dirs):
                errors.append("task {} names skill /{} which does not exist".format(task_id, skill.group(1)))
        gate = section["gate"]
        # A section built by hand, or one that is itself the tests, has no gate of its own.
        if re.search(r"outside the loop|\bTests\b", section["title"]):
            continue
        if not gate.strip():
            errors.append("{} has tasks but no gate".format(where))
            continue
        for category in ("Cat 1", "Cat 2", "Cat 3"):
            if category not in gate:
                errors.append("{}: gate has no checker for {}".format(where, category))
        if not EVIDENCE.search(gate):
            errors.append("{}: gate names no evidence file".format(where))
    return errors


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("tasks")
    p.add_argument("--skills-dir", action="append", help="may be given more than once")
    args = p.parse_args()
    errors = lint(Path(args.tasks).read_text(), args.skills_dir)
    if errors:
        sys.exit("\n".join("- " + e for e in errors))
    print("OK")


if __name__ == "__main__":
    main()
