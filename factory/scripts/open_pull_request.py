#!/usr/bin/env python3
"""Push a work item's branch to GitHub and open a pull request for it.

    open_pull_request.py --repo CHECKOUT --github owner/name --branch factory/GH12 --target main \\
        --title "..." --spec path/to/spec [--issue 12] [--dry-run]

Uses the `gh` login on this machine. It never merges and never pushes to the
target branch: the branch must start with `factory/`.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

ENV = {k: v for k, v in os.environ.items() if k not in ("GITHUB_TOKEN", "GH_TOKEN")}
ENV["GIT_TERMINAL_PROMPT"] = "0"


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, env=ENV)


def description(args):
    spec, repo = Path(args.spec), Path(args.repo)
    link = lambda path: "[{}](https://github.com/{}/blob/{}/{})".format(
        path.name, args.github, quote(args.branch, safe=""), quote(str(path.relative_to(repo))))
    lines = ["Closes #{}".format(args.issue), ""] if args.issue else []
    lines += ["Built by the software factory on branch `{}`. A person reviews and merges.".format(args.branch), "", "## Spec", ""]
    lines += ["- " + link(spec / name) for name in ("requirements.md", "design.md", "visual-spec.md", "tasks.md", "reproduction.md")
              if (spec / name).exists()]
    evidence = sorted((spec / "evidence").glob("*.md")) if (spec / "evidence").exists() else []
    if evidence:
        lines += ["", "## Evidence", ""] + ["- " + link(path) for path in evidence]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("repo", "github", "branch", "target", "title", "spec"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--issue")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    dry = args.dry_run or bool(os.environ.get("FACTORY_DRY_RUN"))

    if not args.branch.startswith("factory/") or args.branch == args.target:
        sys.exit("open_pull_request: refusing to push `{}`; only factory/* branches are pushed".format(args.branch))
    url = "https://github.com/{}.git".format(args.github)
    push = run(["git", "push"] + (["--dry-run"] if dry else []) + [url, "{0}:{0}".format(args.branch)], cwd=args.repo)
    if push.returncode:
        sys.exit("open_pull_request: push failed:\n{}".format(push.stderr or push.stdout))
    if dry:
        print("dry run: push would do:\n{}\n\ndry run: pull request not created. Its description would be:\n\n{}".format(
            (push.stderr or push.stdout).strip(), description(args)))
        return
    existing = run(["gh", "pr", "list", "--repo", args.github, "--head", args.branch, "--state", "open", "--json", "url"])
    found = json.loads(existing.stdout or "[]")
    if found:
        print("Pull request already open: {}".format(found[0]["url"]))
        return
    created = run(["gh", "pr", "create", "--repo", args.github, "--head", args.branch, "--base", args.target,
                   "--title", args.title, "--body", description(args)])
    if created.returncode:
        sys.exit("open_pull_request: gh pr create failed:\n{}".format(created.stderr or created.stdout))
    print("Pull request opened: {}".format(created.stdout.strip().splitlines()[-1]))


if __name__ == "__main__":
    main()
