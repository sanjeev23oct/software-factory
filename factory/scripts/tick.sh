#!/bin/sh
# One pass of the factory over the named targets: pick up new work, then advance
# everything as far as it can go without a person. Meant to be run on a schedule.
#
#   tick.sh TARGET [TARGET ...]
#
# Only one pass runs at a time. Output goes to .factory/logs/tick.log.
HOME_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$HOME_DIR" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
unset GITHUB_TOKEN GH_TOKEN

mkdir -p .factory/logs
LOCK=.factory/tick.lock
# A pass that died leaves its lock behind. Three hours is longer than any pass should take.
find "$LOCK" -maxdepth 0 -mmin +180 -exec rmdir {} \; 2>/dev/null
if ! mkdir "$LOCK" 2>/dev/null; then
  exit 0
fi
trap 'rmdir "$LOCK"' EXIT

{
  for target in "$@"; do
    echo "== $(date '+%Y-%m-%d %H:%M:%S') $target"
    python3 factory/flow.py --target "$target" poll
    python3 factory/flow.py --target "$target" run
  done
} >> .factory/logs/tick.log 2>&1
