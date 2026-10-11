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
  5. The file says, before its first section, that a maker builds and a
     separate checker verifies.
  6. A task names the skill that fits the files it touches. A skill says what
     it is for with `applies_to:` in its front matter.

Exits 1 and lists every violation, or prints OK.
"""

import argparse
import fnmatch
import re
import sys
from pathlib import Path

TASK = re.compile(r"^- \[[ xX]\] (\d+\.\d+) (.*)$")
RUN = re.compile(r"run:\s*`/([\w-]+)`")
SECTION = re.compile(r"^## (.+)$")
EVIDENCE = re.compile(r"evidence/[\w.\-]+\.md")


PATH = re.compile(r"`([\w./-]*[\w-]+\.[A-Za-z]{1,5})`")


def load_skills(skills_dirs):
    """{name: {"description": ..., "applies_to": [globs]}} for every skill in the given folders."""
    skills = {}
    for folder in skills_dirs or []:
        for path in sorted(Path(folder).glob("*/SKILL.md")):
            meta = {}
            for line in path.read_text().split("---")[1].splitlines() if path.read_text().startswith("---") else []:
                key, _, value = line.partition(":")
                meta[key.strip()] = value.strip()
            skills.setdefault(path.parent.name, {"description": meta.get("description", ""),
                                                 "applies_to": [g.strip() for g in meta.get("applies_to", "").split(",") if g.strip()]})
    return skills


def parse(text):
    """Returns sections as dicts: title, tasks [(id, line)], blocks {id: the task and its sub-items}, gate text."""
    sections, current, in_gate, last = [], None, False, None
    for line in text.splitlines():
        heading = SECTION.match(line)
        if heading:
            current = {"title": heading.group(1).strip(), "tasks": [], "blocks": {}, "gate": ""}
            last = None
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
                last = task.group(1)
                current["blocks"][last] = line
            elif last and line.startswith((" ", "\t")):
                current["blocks"][last] += "\n" + line
    return [s for s in sections if s["tasks"]]


def lint(text, skills_dirs):
    errors, skills = [], load_skills(skills_dirs)
    preamble = text.split("\n## ", 1)[0].lower()
    if "maker" not in preamble or "checker" not in preamble:
        errors.append("the file does not say, before its first section, that a maker builds and a separate checker verifies")
    owners = lambda path: [name for name, meta in skills.items() if any(fnmatch.fnmatch(path, g) for g in meta["applies_to"])]
    for section in parse(text):
        where = 'section "{}"'.format(section["title"][:50])
        for task_id, line in section["tasks"]:
            skill = RUN.search(line)
            if not skill:
                errors.append("task {} names no skill (expected: → run: `/skill`)".format(task_id))
            elif skills_dirs and skill.group(1) not in skills:
                errors.append("task {} names skill /{} which does not exist".format(task_id, skill.group(1)))
            elif skills[skill.group(1)]["applies_to"] if skills_dirs else False:
                # The task touches a file that another skill is for.
                for path in sorted(set(PATH.findall(section["blocks"].get(task_id, line)))):
                    fits = owners(path)
                    if fits and skill.group(1) not in fits:
                        errors.append("task {} names /{} but touches `{}`, which /{} is for".format(task_id, skill.group(1), path, fits[0]))
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
