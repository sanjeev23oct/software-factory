#!/usr/bin/env python3
"""Post a comment on an issue: how the factory tells a person a gate is waiting for them.

    post_issue_note.py --source gitlab --project group/repo [--host gitlab.example.com] --ref 12 --file note.md
    post_issue_note.py --source github --repo owner/name --ref 12 --file note.md

GitLab writes with FACTORY_GITLAB_TOKEN (or the Keychain on a Mac). GitHub writes
with FACTORY_GITHUB_TOKEN, or the `gh` login. It only comments: it never changes
labels, assignees or state. With FACTORY_DRY_RUN set it prints the comment instead.
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).parent))
from open_merge_request import token_for  # noqa: E402


def post(url, headers, body):
    request = urllib.request.Request(url, method="POST", data=json.dumps(body).encode(),
                                     headers=dict(headers, **{"Content-Type": "application/json"}))
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        sys.exit("post_issue_note: {} said {}: {}".format(url, e.code, e.read().decode()[:300]))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", required=True, choices=["gitlab", "github"])
    p.add_argument("--project"), p.add_argument("--host"), p.add_argument("--repo")
    p.add_argument("--ref", required=True)
    p.add_argument("--file", required=True)
    args = p.parse_args()
    body = Path(args.file).read_text()
    if os.environ.get("FACTORY_DRY_RUN"):
        return print("dry run: would comment on #{}:\n\n{}".format(args.ref, body))
    if args.source == "gitlab":
        host = args.host or "gitlab.com"
        post("https://{}/api/v4/projects/{}/issues/{}/notes".format(host, quote(args.project, safe=""), args.ref),
             {"PRIVATE-TOKEN": token_for(host)}, {"body": body})
    elif os.environ.get("FACTORY_GITHUB_TOKEN"):
        post("https://api.github.com/repos/{}/issues/{}/comments".format(args.repo, args.ref),
             {"Authorization": "Bearer " + os.environ["FACTORY_GITHUB_TOKEN"], "Accept": "application/json"}, {"body": body})
    else:
        env = {k: v for k, v in os.environ.items() if k not in ("GITHUB_TOKEN", "GH_TOKEN")}
        proc = subprocess.run(["gh", "api", "-X", "POST", "repos/{}/issues/{}/comments".format(args.repo, args.ref),
                               "--input", "-"], input=json.dumps({"body": body}), text=True, capture_output=True, env=env)
        if proc.returncode:
            sys.exit("post_issue_note: gh api failed: {}".format((proc.stderr or proc.stdout).strip()[:300]))
    print("Commented on #{}".format(args.ref))


if __name__ == "__main__":
    main()
