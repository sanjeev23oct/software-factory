#!/usr/bin/env python3
"""Pass only when a review file records an approval.

    check_verdict.py path/to/review.md

The file must contain a line `Verdict: APPROVE`. Anything else fails and the
review is printed, so the factory can send it back to the stage that did the work.
"""

import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.exists():
    sys.exit("{} was not written".format(path.name))
text = path.read_text()
if not re.search(r"^Verdict:\s*APPROVE\s*$", text, re.M):
    sys.exit("The review did not approve.\n\n" + text)
print("OK")
