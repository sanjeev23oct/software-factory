#!/usr/bin/env python3
"""A Claude Code PreToolUse hook: refuse a shell command that names a file agents may not read.

The factory denies Read on these paths through Claude Code's own permissions; this closes the
other door, a command such as `cat .env` or `git show HEAD:secrets/prod.json`. The patterns come
from FACTORY_DENY_READ (JSON list of globs). Exit 2 blocks the command and tells the agent why.
"""

import fnmatch
import json
import os
import re
import sys


def main():
    patterns = json.loads(os.environ.get("FACTORY_DENY_READ") or "[]")
    try:
        command = json.load(sys.stdin).get("tool_input", {}).get("command", "")
    except ValueError:
        return 0
    for word in re.split(r"[\s'\"=:;|&<>()]+", command):
        word = word.strip().lstrip("./")
        if word and any(fnmatch.fnmatch(word, p) or fnmatch.fnmatch(os.path.basename(word), p.split("/")[-1])
                        for p in patterns):
            print("The factory does not let agents read {}: it may hold secrets or personal data. "
                  "Work without it, and say so if the task cannot.".format(word), file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
