#!/bin/sh
# One pass of the factory on a CI runner. The runner starts empty, so the pass
# restores the factory's progress, works, and saves it again:
#
#   ci_tick.sh [TARGET ...]     with no targets: every pipeline switched to pick up work automatically
#
#   1. pull the progress from the `factory-state` branch
#   2. for each pipeline: pick up new issues, apply `/approve` comments, run the agents,
#      push the work branches, and ask for approval on gates that just opened
#   3. push the progress back
#
# Run it from the factory project: a repository that holds targets/ (your pipelines).
# The settings come from CI variables; see docs/run-in-gitlab.md.
set -u
SF="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="${FACTORY_WORK_DIR:-$PWD/.factory-work}"
export FACTORY_TARGETS_DIR="${FACTORY_TARGETS_DIR:-$PWD/targets}"
export FACTORY_STATE_DIR="$WORK/state" FACTORY_REPOS_DIR="$WORK/repos"
# Commits on work branches need a name. The factory signs as itself.
export GIT_AUTHOR_NAME="${GIT_AUTHOR_NAME:-software factory}" GIT_AUTHOR_EMAIL="${GIT_AUTHOR_EMAIL:-factory@localhost}"
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME" GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"
if [ -n "${ANTHROPIC_API_KEY:-}" ] && [ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
  echo "note: both ANTHROPIC_API_KEY and CLAUDE_CODE_OAUTH_TOKEN are set; the API key wins and is billed per token"
fi

flow() { python3 "$SF/factory/flow.py" --target "$target" "$@"; }

python3 "$SF/factory/cloud.py" state-pull || exit 1
if [ $# -eq 0 ]; then
  set -- $(python3 "$SF/factory/flow.py" scheduled)
fi
[ $# -eq 0 ] && echo "no pipeline is switched on (\"auto\": true in its factory.json)"
for target in "$@"; do
  echo "== $(date -u '+%Y-%m-%d %H:%M:%S') UTC  $target"
  # One pipeline failing must not stop the others, or lose the progress already made.
  flow poll || echo "$target: poll failed"
  flow gates || echo "$target: reading approvals failed"
  flow run || echo "$target: run failed"
  flow publish || echo "$target: pushing work branches failed"
  flow gates || echo "$target: asking for approval failed"
  flow status
done
python3 "$SF/factory/cloud.py" state-push
