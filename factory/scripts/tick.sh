#!/bin/sh
# One pass of the factory over the named targets: pick up new work, then advance
# everything as far as it can go without a person. Meant to be run on a schedule.
#
#   tick.sh [TARGET ...]     with no targets: every factory switched to pick up work automatically
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

# Keep the machine awake for as long as this pass runs. A sleeping machine freezes agents mid-task.
if command -v caffeinate >/dev/null 2>&1; then
  caffeinate -i -w $$ &
fi

{
  if [ $# -eq 0 ]; then
    set -- $(python3 factory/flow.py scheduled)
  fi
  for target in "$@"; do
    echo "== $(date '+%Y-%m-%d %H:%M:%S') $target"
    python3 factory/flow.py --target "$target" poll
    python3 factory/flow.py --target "$target" run
  done
} >> .factory/logs/tick.log 2>&1
