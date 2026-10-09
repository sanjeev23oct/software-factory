#!/usr/bin/env python3
"""Software factory orchestrator.

Moves issues through triage -> spec -> implement -> review -> merge. Agents
(headless Claude Code) do the work inside a stage. Labels on the issue are the
state machine, and the readiness labels and the merge are applied by a human.

    factory.py status
    factory.py run [ID]              advance as far as agents may go
    factory.py label ID LABEL        human gate (prefix with - to remove)
    factory.py merge ID              human gate
    factory.py new "title" [--body]  file an issue
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ISSUES = ROOT / "issues"
WORKTREES = ROOT / ".factory" / "worktrees"
RUNS = ROOT / ".factory" / "runs"
MAIN = "main"
MAX_REVIEW_ROUNDS = 3
BUDGET_USD = os.environ.get("FACTORY_MAX_BUDGET_USD", "3")
MODEL = os.environ.get("FACTORY_MODEL")

# Labels only a human applies. Agents recommend, they never set these.
READINESS = ("ready-to-spec", "ready-to-implement")
BLOCKING = ("needs-info", "reserved-internal", "needs-human", "duplicate")


class FactoryError(Exception):
    pass


def sh(cmd, cwd=ROOT, check=True):
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True)
    if check and proc.returncode != 0:
        raise FactoryError("{} failed:\n{}".format(" ".join(cmd), proc.stderr or proc.stdout))
    return proc


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


# --- issues ----------------------------------------------------------------


class Issue:
    def __init__(self, path):
        self.path = Path(path)
        self.id = self.path.stem
        _, front, self.body = self.path.read_text().split("---\n", 2)
        self.meta = {}
        for line in front.splitlines():
            key, _, value = line.partition(":")
            self.meta[key.strip()] = value.strip()

    @property
    def labels(self):
        return [l.strip() for l in self.meta.get("labels", "").split(",") if l.strip()]

    @property
    def title(self):
        return self.meta.get("title", "")

    def has(self, *labels):
        return any(l in self.labels for l in labels)

    def relabel(self, add=(), remove=()):
        labels = [l for l in self.labels if l not in remove]
        labels += [l for l in add if l not in labels]
        self.meta["labels"] = ", ".join(labels)

    def comment(self, who, text):
        self.body = self.body.rstrip() + "\n\n---\n**{}** · {}\n\n{}\n".format(who, now(), text.strip())

    def save(self, message):
        front = "".join("{}: {}\n".format(k, v) for k, v in self.meta.items())
        self.path.write_text("---\n{}---\n{}".format(front, self.body))
        rel = str(self.path.relative_to(ROOT))
        sh(["git", "add", rel])
        if sh(["git", "diff", "--cached", "--quiet", "--", rel], check=False).returncode:
            sh(["git", "commit", "-q", "-m", "{}: {}".format(self.id, message), "--", rel])

    def text(self):
        return "# {}: {}\nlabels: {}\n\n{}".format(self.id, self.title, ", ".join(self.labels), self.body)


def load(issue_id):
    path = ISSUES / "{}.md".format(issue_id)
    if not path.exists():
        raise FactoryError("no such issue: {}".format(issue_id))
    return Issue(path)


def all_issues():
    paths = sorted(ISSUES.glob("GH*.md"), key=lambda p: int(p.stem[2:]))
    return [Issue(p) for p in paths]


# --- workspace -------------------------------------------------------------


def branch_of(issue):
    return "factory/{}".format(issue.id)


def worktree(issue, create=True):
    """Each issue gets its own branch in its own worktree, so agents never
    work in the maintainer's checkout."""
    wt = WORKTREES / issue.id
    if wt.exists() or not create:
        return wt
    WORKTREES.mkdir(parents=True, exist_ok=True)
    branch = branch_of(issue)
    exists = sh(["git", "rev-parse", "--verify", "-q", branch], check=False).returncode == 0
    sh(["git", "worktree", "add", str(wt)] + ([branch] if exists else ["-b", branch, MAIN]))
    return wt


def spec_files(issue):
    base = worktree(issue, create=False) / "specs" / issue.id
    return base / "product.md", base / "tech.md"


def has_specs(issue):
    return all(p.exists() for p in spec_files(issue))


def commit_branch(issue, message):
    wt = worktree(issue)
    sh(["git", "add", "-A"], cwd=wt)
    if sh(["git", "diff", "--cached", "--quiet"], cwd=wt, check=False).returncode == 0:
        return False
    sh(["git", "commit", "-q", "-m", "{}: {}".format(issue.id, message)], cwd=wt)
    return True


def presubmit(cwd):
    proc = sh(["./script/presubmit"], cwd=cwd, check=False)
    tail = "\n".join((proc.stdout + proc.stderr).strip().splitlines()[-25:])
    return proc.returncode == 0, tail


# --- agents ----------------------------------------------------------------


def runs_for(issue, stage):
    return sorted((RUNS / issue.id).glob("{}-*.json".format(stage)))


def last_output(issue, stage):
    runs = runs_for(issue, stage)
    return json.loads(runs[-1].read_text())["output"] if runs else None


def record(issue, stage, payload):
    out_dir = RUNS / issue.id
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "{}-{}.json".format(stage, len(runs_for(issue, stage)) + 1)
    path.write_text(json.dumps(payload, indent=2))


def run_agent(issue, stage, agent, prompt, cwd, schema, mode="default", allowed=()):
    """Run one headless Claude Code agent and return its structured output.

    The agent's tools come from .claude/agents/<agent>.md. Only project
    settings are loaded so the run does not depend on the operator's own setup.
    """
    cmd = ["claude", "-p", prompt, "--agent", agent, "--output-format", "json",
           "--json-schema", json.dumps(schema), "--setting-sources", "project",
           "--permission-mode", mode, "--max-budget-usd", BUDGET_USD]
    if MODEL:
        cmd += ["--model", MODEL]
    if allowed:
        cmd += ["--allowedTools"] + list(allowed)
    print("  [{}] {} agent working...".format(issue.id, agent), flush=True)
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True)
    try:
        data = json.loads(proc.stdout)
    except ValueError:
        raise FactoryError("{} agent gave no JSON:\n{}".format(agent, (proc.stdout + proc.stderr)[-2000:]))
    output = data.get("structured_output")
    record(issue, stage, {"agent": agent, "cost_usd": data.get("total_cost_usd", 0),
                          "turns": data.get("num_turns"), "output": output,
                          "result": data.get("result")})
    if data.get("is_error") or output is None:
        raise FactoryError("{} agent failed: {}".format(agent, str(data.get("result"))[:2000]))
    return output


def obj(required, **props):
    return {"type": "object", "properties": props, "required": required, "additionalProperties": False}


STR = {"type": "string"}
STRS = {"type": "array", "items": STR}

TRIAGE_SCHEMA = obj(
    ["type", "area", "repro", "recommendation", "comment"],
    type={"enum": ["bug", "feature", "question"]},
    area={"enum": ["cli", "storage", "docs"]},
    repro={"enum": ["confirmed", "unconfirmed", "not-applicable"]},
    duplicate_of={"type": ["string", "null"]},
    recommendation={"enum": ["ready-to-spec", "ready-to-implement", "needs-info", "none"]},
    comment=STR,
)
SPEC_SCHEMA = obj(["summary", "open_questions"], summary=STR, open_questions=STRS)
IMPLEMENT_SCHEMA = obj(
    ["summary", "tests_added", "presubmit_passed"],
    summary=STR, tests_added=STRS, presubmit_passed={"type": "boolean"}, spec_deviations=STRS,
)
REVIEW_SCHEMA = obj(
    ["verdict", "summary", "findings", "invariants"],
    verdict={"enum": ["approve", "request_changes"]},
    summary=STR,
    findings={"type": "array", "items": obj(
        ["severity", "file", "comment"],
        severity={"enum": ["blocking", "nit"]}, file=STR, line={"type": "integer"}, comment=STR)},
    invariants={"type": "array", "items": obj(
        ["id", "satisfied", "evidence"], id=STR, satisfied={"type": "boolean"}, evidence=STR)},
)


# --- stages ----------------------------------------------------------------


def triage(issue):
    out = run_agent(issue, "triage", "triager",
                    "Triage this issue.\n\n" + issue.text(), ROOT, TRIAGE_SCHEMA,
                    allowed=["Bash(python3:*)"])
    add = ["triaged", out["type"], "area:" + out["area"]]
    if out["type"] == "bug":
        add.append("repro:" + out["repro"])
    if out["recommendation"] == "needs-info":
        add.append("needs-info")
    if out.get("duplicate_of"):
        add.append("duplicate")
    issue.relabel(add=add, remove=["needs-triage", "bug", "feature", "question"])
    issue.comment("factory-triage", "{}\n\nRecommended readiness: `{}`".format(out["comment"], out["recommendation"]))
    issue.save("triaged")


def spec(issue):
    wt = worktree(issue)
    out = run_agent(issue, "spec", "spec-writer",
                    "Write the product spec and tech spec for issue {}.\n\n{}".format(issue.id, issue.text()),
                    wt, SPEC_SCHEMA, mode="acceptEdits")
    if not has_specs(issue):
        raise FactoryError("spec-writer did not produce both spec files for {}".format(issue.id))
    commit_branch(issue, "product and tech spec")
    questions = "\n".join("- " + q for q in out["open_questions"]) or "None"
    issue.relabel(add=["spec-in-review"])
    issue.comment("factory-spec", "{}\n\nSpecs: `{}`\n\nOpen questions:\n{}".format(
        out["summary"], spec_files(issue)[0].parent.relative_to(ROOT), questions))
    issue.save("spec written")


def implement(issue):
    wt = worktree(issue)
    prompt = "Implement issue {}.\n\n{}".format(issue.id, issue.text())
    if has_specs(issue):
        prompt += "\n\nSpecs are in specs/{}/. They are the contract.".format(issue.id)
    feedback = last_output(issue, "review") if issue.has("changes-requested") else None
    if feedback:
        prompt += "\n\nYour previous attempt was reviewed and changes were requested. " \
                  "Address every finding:\n" + json.dumps(feedback, indent=2)
    out = run_agent(issue, "implement", "implementer", prompt, wt, IMPLEMENT_SCHEMA, mode="acceptEdits",
                    allowed=["Bash(./script/presubmit)", "Bash(python3:*)", "Bash(git diff:*)", "Bash(git status:*)"])
    if not commit_branch(issue, issue.title) and not feedback:
        raise FactoryError("implementer changed nothing for {}".format(issue.id))
    note = out["summary"]
    if out.get("spec_deviations"):
        note += "\n\nDeviations from tech spec:\n" + "\n".join("- " + d for d in out["spec_deviations"])
    issue.relabel(add=["in-review"], remove=["changes-requested"])
    issue.comment("factory-implement", "{}\n\nBranch: `{}`".format(note, branch_of(issue)))
    issue.save("implemented")


def review(issue):
    wt = worktree(issue)
    round_no = len(runs_for(issue, "review")) + 1
    ok, tail = presubmit(wt)
    if ok:
        prompt = "Review the branch for issue {}. Presubmit passes.\n\n{}".format(issue.id, issue.text())
        if has_specs(issue):
            prompt += "\n\nSpecs are in specs/{}/. Check every invariant in product.md.".format(issue.id)
        out = run_agent(issue, "review", "reviewer", prompt, wt, REVIEW_SCHEMA,
                        allowed=["Bash(git diff:*)", "Bash(git log:*)", "Bash(git show:*)", "Bash(python3:*)"])
    else:
        # A red presubmit is not worth an agent's time. Bounce it straight back.
        out = {"verdict": "request_changes", "summary": "Presubmit fails.", "invariants": [],
               "findings": [{"severity": "blocking", "file": "script/presubmit", "comment": tail}]}
        record(issue, "review", {"agent": "presubmit", "cost_usd": 0, "output": out})

    blocking = [f for f in out["findings"] if f["severity"] == "blocking"]
    unmet = [i for i in out["invariants"] if not i["satisfied"]]
    approved = out["verdict"] == "approve" and not blocking and not unmet
    lines = ["Review round {}: **{}**".format(round_no, "approve" if approved else "request changes"), "", out["summary"]]
    for f in out["findings"]:
        where = f["file"] + (":{}".format(f["line"]) if f.get("line") else "")
        lines.append("- [{}] `{}` {}".format(f["severity"], where, f["comment"]))
    if out["invariants"]:
        lines.append("\nInvariants: {}/{} satisfied".format(len(out["invariants"]) - len(unmet), len(out["invariants"])))

    if approved:
        issue.relabel(add=["agent-approved"], remove=["in-review"])
    else:
        issue.relabel(add=["changes-requested"], remove=["in-review"])
        if round_no >= MAX_REVIEW_ROUNDS:
            issue.relabel(add=["needs-human"])
            lines.append("\nReview limit of {} rounds reached. Escalating to a maintainer.".format(MAX_REVIEW_ROUNDS))
    issue.comment("factory-review", "\n".join(lines))
    issue.save("review round {}".format(round_no))


def next_action(issue):
    """Who moves this issue next, and how. Returns (actor, stage or None, description)."""
    if issue.meta.get("state") == "closed":
        return "-", None, "merged" if issue.has("merged") else "closed"
    if issue.has("needs-triage"):
        return "agent", triage, "triage"
    for label in BLOCKING:
        if issue.has(label):
            return "human", None, "blocked: " + label
    if issue.has("agent-approved"):
        return "human", None, "final review, then `merge {}`".format(issue.id)
    if issue.has("in-review"):
        return "agent", review, "review"
    if issue.has("changes-requested"):
        return "agent", implement, "address review feedback"
    if issue.has("ready-to-implement"):
        return "agent", implement, "implement"
    if issue.has("spec-in-review"):
        return "human", None, "review specs, then `label {} ready-to-implement`".format(issue.id)
    if issue.has("ready-to-spec"):
        return "agent", spec, "write specs"
    return "human", None, "apply a readiness label"


# --- commands --------------------------------------------------------------


def cmd_status(args):
    rows = []
    for issue in all_issues():
        actor, _, what = next_action(issue)
        cost = sum(json.loads(p.read_text()).get("cost_usd") or 0 for p in (RUNS / issue.id).glob("*.json"))
        rows.append((issue.id, issue.title[:38], actor, what, "${:.2f}".format(cost), ", ".join(issue.labels)))
    widths = [max(len(r[i]) for r in rows + [("ID", "TITLE", "NEXT", "ACTION", "COST", "")]) for i in range(5)]
    fmt = "  ".join("{:<%d}" % w for w in widths) + "  {}"
    print(fmt.format("ID", "TITLE", "NEXT", "ACTION", "COST", "LABELS"))
    for row in rows:
        print(fmt.format(*row))


def cmd_run(args):
    issues = [load(args.id)] if args.id else all_issues()
    for issue in issues:
        while True:
            actor, stage, what = next_action(issue)
            if actor != "agent":
                print("{}: waiting on {} - {}".format(issue.id, actor, what) if actor == "human"
                      else "{}: {}".format(issue.id, what))
                break
            print("{}: {}".format(issue.id, what))
            try:
                stage(issue)
            except FactoryError as e:
                print("{}: stopped - {}".format(issue.id, e))
                break
            issue = load(issue.id)


def cmd_label(args):
    issue = load(args.id)
    if args.label.startswith("-"):
        issue.relabel(remove=[args.label[1:]])
        issue.comment("maintainer", "Removed label `{}`.".format(args.label[1:]))
        issue.save("label removed")
        return
    label = args.label
    if label in READINESS:
        blockers = [b for b in BLOCKING if issue.has(b)]
        if blockers:
            raise FactoryError("{} is blocked by: {}".format(issue.id, ", ".join(blockers)))
        if not issue.has("triaged"):
            raise FactoryError("{} has not been triaged".format(issue.id))
    if label == "ready-to-spec" and not issue.has("feature"):
        raise FactoryError("only features are specced; a bug goes straight to ready-to-implement")
    if label == "ready-to-implement":
        if issue.has("feature") and not has_specs(issue):
            raise FactoryError("{} is a feature with no specs; label it ready-to-spec first".format(issue.id))
        issue.relabel(remove=["ready-to-spec", "spec-in-review"])
    issue.relabel(add=[label])
    issue.comment("maintainer", "Applied label `{}`.".format(label))
    issue.save("labelled " + label)
    print("{}: {}".format(issue.id, ", ".join(issue.labels)))


def cmd_merge(args):
    issue = load(args.id)
    if not issue.has("agent-approved"):
        raise FactoryError("{} has not passed agent review".format(issue.id))
    if sh(["git", "status", "--porcelain"]).stdout.strip():
        raise FactoryError("main checkout has uncommitted changes")
    title = "Merge {}: {}".format(issue.id, issue.title)
    if sh(["git", "merge", "--no-ff", "--no-commit", branch_of(issue)], check=False).returncode != 0:
        sh(["git", "merge", "--abort"], check=False)
        problem = "Merge conflicts with main."
    else:
        # Verify the merged result, not the branch: main may have moved on.
        ok, tail = presubmit(ROOT)
        if ok:
            sh(["git", "commit", "-q", "-m", title])
            sh(["git", "worktree", "remove", "--force", str(worktree(issue, create=False))])
            sh(["git", "branch", "-q", "-d", branch_of(issue)])
            issue.relabel(add=["merged"], remove=["agent-approved", "ready-to-implement"])
            issue.meta["state"] = "closed"
            issue.comment("maintainer", "Approved and merged.")
            issue.save("merged")
            print("{}: merged".format(issue.id))
            return
        sh(["git", "merge", "--abort"], check=False)
        problem = "Presubmit fails on the merged result:\n\n```\n{}\n```".format(tail)
    issue.relabel(add=["needs-human"], remove=["agent-approved"])
    issue.comment("factory-merge", problem)
    issue.save("merge failed")
    raise FactoryError("{}: {}".format(issue.id, problem.splitlines()[0]))


def cmd_new(args):
    number = max([int(i.id[2:]) for i in all_issues()] or [0]) + 1
    path = ISSUES / "GH{}.md".format(number)
    path.write_text("---\ntitle: {}\nauthor: {}\nstate: open\nlabels: needs-triage\n---\n{}\n".format(
        args.title, os.environ.get("USER", "unknown"), args.body))
    Issue(path).save("filed")
    print(path.stem)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    p = sub.add_parser("run"); p.add_argument("id", nargs="?"); p.set_defaults(fn=cmd_run)
    p = sub.add_parser("label"); p.add_argument("id"); p.add_argument("label"); p.set_defaults(fn=cmd_label)
    p = sub.add_parser("merge"); p.add_argument("id"); p.set_defaults(fn=cmd_merge)
    p = sub.add_parser("new"); p.add_argument("title"); p.add_argument("--body", default=""); p.set_defaults(fn=cmd_new)
    args = parser.parse_args()
    try:
        args.fn(args)
    except FactoryError as e:
        sys.exit("error: {}".format(e))


if __name__ == "__main__":
    main()
