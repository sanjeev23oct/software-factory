#!/usr/bin/env python3
"""Post the factory's review on a GitLab merge request, as one comment that is updated in place.

    post_mr_note.py --host gitlab.example.com --project group/repo --ref 7 --sha abc123 FILE [FILE ...] [--dry-run]

The files are joined into one comment. Files that do not exist are skipped. A
previous factory comment on the same request is edited, so a request collects
one comment however many times it is reviewed.

Writes with the token from the macOS Keychain (account `software-factory`,
service = the host) or FACTORY_GITLAB_TOKEN. It comments. It never approves,
merges, or changes labels.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).parent))
from open_merge_request import token_for  # noqa: E402

MARKER = "<!-- software-factory:review -->"


def api(host, token, method, path, data=None):
    request = urllib.request.Request("https://{}/api/v4/{}".format(host, path), method=method,
                                     data=json.dumps(data).encode() if data else None,
                                     headers={"PRIVATE-TOKEN": token, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        sys.exit("post_mr_note: GitLab said {} for {} {}: {}".format(e.code, method, path, e.read().decode()[:300]))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("host", "project", "ref"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--sha", default="")
    p.add_argument("files", nargs="+")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    parts = [Path(f).read_text().strip() for f in args.files if Path(f).exists()]
    if not parts:
        sys.exit("post_mr_note: none of the report files exist")
    body = "{}\n{}\n\n---\n_Software factory review of `{}`. A script checked the process; an agent reviewed the code only if the process passed. A person decides whether to merge._".format(
        MARKER, "\n\n".join(parts), args.sha[:8] or "this request")
    if args.dry_run or os.environ.get("FACTORY_DRY_RUN"):
        print("dry run: nothing posted. The comment would be:\n")
        print(body)
        return
    token = token_for(args.host)
    base = "projects/{}/merge_requests/{}/notes".format(quote(args.project, safe=""), args.ref)
    mine = [n for n in api(args.host, token, "GET", base + "?per_page=100") if MARKER in n["body"]]
    if mine:
        api(args.host, token, "PUT", "{}/{}".format(base, mine[-1]["id"]), {"body": body})
        print("Updated the review comment on !{}".format(args.ref))
    else:
        api(args.host, token, "POST", base, {"body": body})
        print("Posted the review comment on !{}".format(args.ref))


if __name__ == "__main__":
    main()
