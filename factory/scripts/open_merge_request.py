#!/usr/bin/env python3
"""Push a work item's branch to GitLab and open a merge request for it.

    open_merge_request.py --repo CHECKOUT --host gitlab.example.com --project group/repo \\
        --branch factory/GL12 --target main --title "..." --spec path/to/spec [--issue 12] [--dry-run]

This is the only script in the factory that writes to GitLab. It never merges
and never pushes to the target branch: the branch must start with `factory/`.

The token is read from the macOS Keychain (account `software-factory`, service
= the host), or from FACTORY_GITLAB_TOKEN. It is never printed, never passed on
a command line, and never written to disk.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote


def token_for(host):
    token = os.environ.get("FACTORY_GITLAB_TOKEN")
    if not token:
        try:
            proc = subprocess.run(["security", "find-generic-password", "-a", "software-factory", "-s", host, "-w"],
                                  text=True, capture_output=True)
            token = proc.stdout.strip()
        except FileNotFoundError:
            pass   # not a Mac: there is no Keychain, only the environment variable
    if not token:
        sys.exit("open_merge_request: no token. Set FACTORY_GITLAB_TOKEN, or on a Mac add one with:\n"
                 "  security add-generic-password -a software-factory -s {} -w".format(host))
    return token


def api(host, token, method, path, data=None):
    request = urllib.request.Request("https://{}/api/v4/{}".format(host, path), method=method,
                                     data=json.dumps(data).encode() if data else None,
                                     headers={"PRIVATE-TOKEN": token, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        sys.exit("open_merge_request: GitLab said {} for {} {}: {}".format(e.code, method, path, e.read().decode()[:300]))


def git(repo, *args, env=None):
    return subprocess.run(["git"] + list(args), cwd=str(repo), text=True, capture_output=True, env=env)


def push(repo, host, project, branch, token, dry_run):
    """Push with the token handed to git through an askpass helper, so it never appears in a command line."""
    with tempfile.TemporaryDirectory() as tmp:
        helper = Path(tmp) / "askpass"
        helper.write_text('#!/bin/sh\ncase "$1" in Username*) echo oauth2 ;; *) echo "$FACTORY_PUSH_TOKEN" ;; esac\n')
        helper.chmod(0o700)
        env = dict(os.environ, GIT_ASKPASS=str(helper), FACTORY_PUSH_TOKEN=token, GIT_TERMINAL_PROMPT="0")
        url = "https://{}/{}.git".format(host, project)
        args = ["-c", "credential.helper=", "push"] + (["--dry-run"] if dry_run else []) + [url, "{0}:{0}".format(branch)]
        proc = git(repo, *args, env=env)
    if proc.returncode != 0:
        sys.exit("open_merge_request: push failed:\n{}".format((proc.stderr or proc.stdout).replace(token, "***")))
    return (proc.stderr or proc.stdout).strip()


def description(args, web_url):
    spec, repo = Path(args.spec), Path(args.repo)
    rel = spec.relative_to(repo)
    link = lambda path: "[{}]({}/-/blob/{}/{})".format(path.name, web_url, quote(args.branch, safe=""), quote(str(path.relative_to(repo))))
    lines = ["Closes #{}".format(args.issue), ""] if args.issue else []
    lines += ["Built by the software factory on branch `{}`. A person reviews and merges.".format(args.branch), "", "## Spec", ""]
    lines += ["- " + link(spec / name) for name in ("requirements.md", "design.md", "tasks.md") if (spec / name).exists()]
    evidence = sorted((spec / "evidence").glob("*.md")) if (spec / "evidence").exists() else []
    if evidence:
        lines += ["", "## Evidence", ""] + ["- " + link(path) for path in evidence]
    lines += ["", "Spec folder: `{}`".format(rel)]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("repo", "host", "project", "branch", "target", "title", "spec"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--issue")
    p.add_argument("--dry-run", action="store_true", help="check the token and the push without changing anything")
    args = p.parse_args()

    if not args.branch.startswith("factory/") or args.branch == args.target:
        sys.exit("open_merge_request: refusing to push `{}`; only factory/* branches are pushed".format(args.branch))
    token = token_for(args.host)
    project = api(args.host, token, "GET", "projects/" + quote(args.project, safe=""))
    args.dry_run = args.dry_run or bool(os.environ.get("FACTORY_DRY_RUN"))
    pushed = push(args.repo, args.host, args.project, args.branch, token, args.dry_run)
    if args.dry_run:
        print("dry run: token accepted for {}; push would do:\n{}".format(project["path_with_namespace"], pushed))
        print("dry run: merge request not created. Its description would be:\n\n" + description(args, project["web_url"]))
        return

    base = "projects/{}/merge_requests".format(project["id"])
    existing = api(args.host, token, "GET", "{}?state=opened&source_branch={}".format(base, quote(args.branch, safe="")))
    if existing:
        print("Merge request already open: {}".format(existing[0]["web_url"]))
        return
    created = api(args.host, token, "POST", base, {
        "source_branch": args.branch, "target_branch": args.target, "title": args.title,
        "description": description(args, project["web_url"]), "remove_source_branch": True})
    print("Merge request opened: {}".format(created["web_url"]))


if __name__ == "__main__":
    main()
