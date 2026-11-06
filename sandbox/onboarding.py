#!/usr/bin/env python3
"""Write one client's onboarding page from sandbox/client-onboarding.md.

    python3 sandbox/onboarding.py --client Chris --project clients/software-factory-playground

It writes private/<client>-onboarding.md, which git ignores. The page holds no
usernames or passwords: send those to the client separately.
"""

import argparse
import re
from pathlib import Path

HOME = Path(__file__).resolve().parent.parent


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--client", required=True, help="the client's name, as the page greets them")
    p.add_argument("--project", required=True, help="their GitLab project, e.g. clients/acme-portal")
    p.add_argument("--target", help="their pipeline's name; setup.sh names it after the project (default)")
    p.add_argument("--gitlab", default="https://gitlab.justpush.cloud")
    p.add_argument("--preview-host", default="factory.justpush.cloud")
    p.add_argument("--sample-project", default="clients/factory-demo")
    p.add_argument("--sample-spec", default="specs/1-build-a-crm-dashboard-for-my-customers")
    p.add_argument("--out", help="default: private/<client>-onboarding.md")
    args = p.parse_args()

    target = args.target or args.project.rsplit("/", 1)[-1]
    sample_target = args.sample_project.rsplit("/", 1)[-1]
    values = {"CLIENT": args.client, "GITLAB": args.gitlab.rstrip("/"), "PROJECT": args.project,
              "SITE": "https://{}/{}".format(args.preview_host, target),
              "SAMPLE_PROJECT": args.sample_project, "SAMPLE_SITE": "https://{}/{}".format(args.preview_host, sample_target),
              "SAMPLE_SPEC": args.sample_spec}
    page = (HOME / "sandbox" / "client-onboarding.md").read_text()
    page = re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], page)
    out = Path(args.out) if args.out else HOME / "private" / "{}-onboarding.md".format(re.sub(r"[^a-z0-9]+", "-", args.client.lower()).strip("-"))
    out.parent.mkdir(exist_ok=True)
    out.write_text(page)
    print("wrote {}".format(out))


if __name__ == "__main__":
    main()
