#!/usr/bin/env python3
"""Say where a person can try an item's branch, for the gate that follows.

    preview_link.py --item GL5 [--branch factory/GL5] [--target NAME]

FACTORY_PREVIEW_URL is the address template, with {item}, {branch} and {target}
filled in, for example https://preview.example.com/{item}/. A preview server
serves each pushed `factory/*` branch there. The branch is pushed at the end of
the pass, so the link says the preview can take a minute to appear.

With no FACTORY_PREVIEW_URL it says so and passes: a preview is a convenience,
not a check.
"""

import argparse
import os


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--item", required=True)
    p.add_argument("--branch")
    p.add_argument("--target", default="")
    args = p.parse_args()
    template = os.environ.get("FACTORY_PREVIEW_URL", "").strip()
    if not template:
        return print("No preview server is set up (FACTORY_PREVIEW_URL is empty).")
    url = template.format(item=args.item, branch=args.branch or "factory/" + args.item, target=args.target)
    print("Try it: {}  (ready about a minute after this pass pushes the branch)".format(url))


if __name__ == "__main__":
    main()
