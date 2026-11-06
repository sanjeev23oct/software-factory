#!/usr/bin/env bash
# Set up the leadership test drive on the self-hosted GitLab, from the VPS.
#
#   cd /path/to/software-factory && git pull
#   GITLAB_TOKEN=glpat-... sandbox/setup.sh
#
# It is safe to run again: every step checks what is already there.
#
# What it does:
#   1. creates the private project sandbox/test-drive-app, seeded with a small
#      task board and an issue template that hands issues to the factory
#   2. adds the factory's bot user, and anyone in INVITE, to that project
#   3. adds the `test-drive` pipeline to the factory project's targets/
#   4. lets a webhook start a factory pass the moment someone files an issue
#      or comments, instead of waiting for the 10-minute schedule
#   5. starts the preview server, so each issue's branch can be tried in a browser
#
# Settings (environment):
#   GITLAB_TOKEN      required. An admin's personal access token with the `api` scope.
#   GITLAB_URL        default https://gitlab.justpush.cloud
#   FACTORY_PROJECT   default ai-sdlc/software-factory
#   SANDBOX_PROJECT   default sandbox/test-drive-app
#   PREVIEW_URL       where people open previews, with {item}. Default http://<this server's IP>:8090/{item}/
#   PREVIEW_PORT      default 8090
#   FACTORY_REF       the factory code the runner uses. Default: this checkout's commit, which must be pushed.
#   FACTORY_BOT_USER  the username behind FACTORY_GITLAB_TOKEN, if that variable is hidden.
#   INVITE            optional. "username:email username:email". Creates the GitLab users that do
#                     not exist yet (prints their first password once) and adds everyone as Developer.
set -euo pipefail

: "${GITLAB_TOKEN:?set GITLAB_TOKEN to an admin personal access token with the api scope}"
GITLAB_URL=${GITLAB_URL:-https://gitlab.justpush.cloud}
GITLAB_URL=${GITLAB_URL%/}
HOST=${GITLAB_URL#https://}; HOST=${HOST#http://}
FACTORY_PROJECT=${FACTORY_PROJECT:-ai-sdlc/software-factory}
SANDBOX_PROJECT=${SANDBOX_PROJECT:-sandbox/test-drive-app}
PREVIEW_PORT=${PREVIEW_PORT:-8090}
SF="$(cd "$(dirname "$0")/.." && pwd)"
FACTORY_REF=${FACTORY_REF:-$(git -C "$SF" rev-parse HEAD)}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

say() { printf '\n== %s\n' "$*"; }
need() { command -v "$1" >/dev/null || { echo "error: $1 is not installed" >&2; exit 1; }; }
for tool in curl git python3 docker; do need "$tool"; done

# Python's urllib is refused by Cloudflare in front of this GitLab, so every API call goes through curl.
api() {
  local method=$1 path=$2; shift 2
  curl -sS --fail-with-body -X "$method" -H "PRIVATE-TOKEN: $GITLAB_TOKEN" "$GITLAB_URL/api/v4/$path" "$@"
}
api_or_empty() { api "$@" 2>/dev/null || true; }
json() { python3 -c "import json,sys; d=json.load(sys.stdin); print(eval(sys.argv[1], {'d': d}))" "$1"; }
enc() { python3 -c "import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=''))" "$1"; }
gitauth() { git -c http.extraHeader="Authorization: Basic $(printf 'oauth2:%s' "$GITLAB_TOKEN" | base64 | tr -d '\n')" "$@"; }

say "Checking the token"
me=$(api GET user)
[ "$(echo "$me" | json "d.get('is_admin', False)")" = "True" ] || { echo "error: GITLAB_TOKEN must belong to an admin" >&2; exit 1; }
echo "signed in as $(echo "$me" | json "d['username']")"
git -C "$SF" fetch -q origin 2>/dev/null || true
if ! git -C "$SF" branch -r --contains "$FACTORY_REF" 2>/dev/null | grep -q .; then
  echo "error: commit $FACTORY_REF is not pushed, so the runner cannot clone it. Push it, or set FACTORY_REF." >&2
  exit 1
fi

say "Sandbox project $SANDBOX_PROJECT"
group=${SANDBOX_PROJECT%/*}; name=${SANDBOX_PROJECT##*/}
gid=$(api_or_empty GET "groups/$(enc "$group")" | json "d['id']" 2>/dev/null || true)
if [ -z "$gid" ]; then
  gid=$(api POST groups --data-urlencode "name=$group" --data-urlencode "path=$group" -d visibility=private | json "d['id']")
  echo "created group $group"
fi
sid=$(api_or_empty GET "projects/$(enc "$SANDBOX_PROJECT")" | json "d['id']" 2>/dev/null || true)
if [ -z "$sid" ]; then
  sid=$(api POST projects --data-urlencode "name=$name" --data-urlencode "path=$name" -d "namespace_id=$gid" \
        -d visibility=private -d default_branch=main | json "d['id']")
  echo "created project $SANDBOX_PROJECT"
fi
if [ "$(api GET "projects/$sid/repository/branches" | json 'len(d)')" = "0" ]; then
  cp -r "$SF/sandbox/app/." "$WORK/app"
  git -C "$WORK/app" init -q -b main
  git -C "$WORK/app" add -A
  git -C "$WORK/app" -c user.name="software factory" -c user.email=factory@localhost commit -qm "Seed the test drive app"
  gitauth -C "$WORK/app" push -q "$GITLAB_URL/$SANDBOX_PROJECT.git" main
  echo "pushed the seed app"
else
  echo "already has code; left as it is"
fi
api_or_empty POST "projects/$sid/labels" -d name=factory --data-urlencode "color=#b3348c" \
  --data-urlencode "description=Hands the issue to the software factory" >/dev/null && echo "label factory ready"

say "Members"
add_member() {   # user id, label
  # members/all counts access inherited from the group; adding a lower role than that is refused with a 400.
  if api_or_empty GET "projects/$sid/members/all/$1" | grep -q '"id"'; then echo "$2 is already a member"; return; fi
  api POST "projects/$sid/members" -d "user_id=$1" -d access_level=30 >/dev/null && echo "added $2 as Developer"
}
fid=$(api GET "projects/$(enc "$FACTORY_PROJECT")" | json "d['id']")
# The factory comments and pushes as whoever owns FACTORY_GITLAB_TOKEN. A hidden variable
# cannot be read back; then say who that is with FACTORY_BOT_USER.
if [ -n "${FACTORY_BOT_USER:-}" ]; then
  bot_user=$FACTORY_BOT_USER
else
  bot_token=$(api GET "projects/$fid/variables/FACTORY_GITLAB_TOKEN" | json "d.get('value') or ''")
  [ -n "$bot_token" ] || { echo "error: cannot read FACTORY_GITLAB_TOKEN; set FACTORY_BOT_USER to its username" >&2; exit 1; }
  bot_user=$(curl -sS --fail-with-body -H "PRIVATE-TOKEN: $bot_token" "$GITLAB_URL/api/v4/user" | json "d['username']")
fi
bot_id=$(api GET "users?username=$(enc "$bot_user")" | json "d[0]['id']")
add_member "$bot_id" "the factory's user @$bot_user"
for entry in ${INVITE:-}; do
  user=${entry%%:*}; email=${entry#*:}
  uid=$(api GET "users?username=$(enc "$user")" | json "d[0]['id'] if d else ''")
  if [ -z "$uid" ]; then
    password=$(python3 -c "import secrets; print(secrets.token_urlsafe(12))")
    uid=$(api POST users --data-urlencode "username=$user" --data-urlencode "name=$user" --data-urlencode "email=$email" \
          --data-urlencode "password=$password" -d skip_confirmation=true | json "d['id']")
    echo "created @$user   first password: $password   (they are asked to change it)"
  fi
  add_member "$uid" "@$user"
done

say "The test-drive pipeline in $FACTORY_PROJECT"
gitauth clone -q "$GITLAB_URL/$FACTORY_PROJECT.git" "$WORK/factory"
gitauth clone -q "$GITLAB_URL/$SANDBOX_PROJECT.git" "$WORK/sandbox"
rm -rf "$WORK/factory/targets/test-drive"
FACTORY_TARGETS_DIR="$WORK/factory/targets" python3 "$SF/factory/flow.py" init test-drive --sample test-drive --repo "$WORK/sandbox" >/dev/null
T="$WORK/factory/targets/test-drive"
cp "$SF/sandbox/target/AGENTS.md" "$SF/sandbox/target/presubmit" "$T/"
python3 - "$T" "$HOST" "$SANDBOX_PROJECT" "$GITLAB_URL" <<'EOF'
import json, sys
from pathlib import Path
home, host, project, url = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
definition = json.loads((home / "factory.json").read_text())
definition["auto"] = True
definition["source"].update(host=host, project=project)
(home / "factory.json").write_text(json.dumps(definition, indent=2) + "\n")
target = json.loads((home / "target.json").read_text())
target.pop("repo", None)
target.update(remote="{}/{}.git".format(url, project), protected=sorted(set(target["protected"]) | {".gitlab/"}))
(home / "target.json").write_text(json.dumps(target, indent=2) + "\n")
EOF
chmod +x "$T/presubmit"
FACTORY_TARGETS_DIR="$WORK/factory/targets" FACTORY_REPOS_DIR="$WORK/repos" FACTORY_STATE_DIR="$WORK/state" \
  FACTORY_GIT_TOKEN="$GITLAB_TOKEN" python3 "$SF/factory/flow.py" --target test-drive validate

# Let a webhook start a pass. Edit the job's rules only if the trigger is not allowed yet.
ci="$WORK/factory/.gitlab-ci.yml"
if [ -f "$ci" ] && ! grep -q 'CI_PIPELINE_SOURCE == "trigger"' "$ci"; then
  if python3 - "$ci" <<'EOF'
import re, sys
path = sys.argv[1]
text = open(path).read()
match = re.search(r'^(\s*- if: \$CI_PIPELINE_SOURCE == "web".*)$', text, re.M)
if not match:
    sys.exit(1)
line = match.group(1)
indent = line[:len(line) - len(line.lstrip())]
text = text.replace(line, line + "\n" + indent + '- if: $CI_PIPELINE_SOURCE == "trigger"     # a webhook: an issue filed or a comment', 1)
open(path, "w").write(text)
EOF
  then echo "allowed webhook-started passes in .gitlab-ci.yml"
  else echo "warning: could not find the \"web\" rule in .gitlab-ci.yml. Add: - if: \$CI_PIPELINE_SOURCE == \"trigger\""
  fi
fi
git -C "$WORK/factory" add -A targets/test-drive .gitlab-ci.yml
git -C "$WORK/factory" update-index --chmod=+x targets/test-drive/presubmit
if git -C "$WORK/factory" diff --cached --quiet; then
  echo "no change to the factory project"
else
  git -C "$WORK/factory" diff --cached --stat
  git -C "$WORK/factory" -c user.name="software factory" -c user.email=factory@localhost commit -qm "Add the test-drive pipeline"
  gitauth -C "$WORK/factory" push -q origin HEAD
  echo "pushed to $FACTORY_PROJECT"
fi

say "Preview server"
if [ -z "${PREVIEW_URL:-}" ]; then
  ip=$(curl -sS -4 --max-time 5 https://ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')
  PREVIEW_URL="http://$ip:$PREVIEW_PORT/{item}/"
fi
network=$(docker inspect gitlab -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' | awk '{print $1}')
existing=$(api GET "projects/$sid/access_tokens" | json "[t['id'] for t in d if t['name'] == 'factory-preview' and t['active']]")
if [ "$existing" = "[]" ] || [ ! -f /data/factory-preview/.env ]; then
  expires=$(python3 -c "import datetime; print(datetime.date.today() + datetime.timedelta(days=364))")
  preview_token=$(api POST "projects/$sid/access_tokens" -d name=factory-preview -d access_level=20 \
                  -d "scopes[]=read_repository" -d "expires_at=$expires" | json "d['token']")
  mkdir -p /data/factory-preview
  umask 077
  printf 'PREVIEW_REPO=http://gitlab/%s.git\nPREVIEW_TOKEN=%s\nPREVIEW_PORT=%s\nGITLAB_NETWORK=%s\n' \
    "$SANDBOX_PROJECT" "$preview_token" "$PREVIEW_PORT" "$network" > /data/factory-preview/.env
  umask 022
fi
cp "$SF/sandbox/preview/compose.yml" "$SF/sandbox/preview/sync.sh" /data/factory-preview/
chmod 755 /data/factory-preview/sync.sh
docker compose -f /data/factory-preview/compose.yml --env-file /data/factory-preview/.env up -d
echo "previews: ${PREVIEW_URL/\{item\}/main} shows the app as it is on main"

say "CI variables on $FACTORY_PROJECT"
setvar() {   # name, value
  if api_or_empty GET "projects/$fid/variables/$1" | grep -q '"key"'; then
    api PUT "projects/$fid/variables/$1" --data-urlencode "value=$2" >/dev/null
  else
    api POST "projects/$fid/variables" -d "key=$1" --data-urlencode "value=$2" >/dev/null
  fi
  echo "$1 = $2"
}
setvar FACTORY_PREVIEW_URL "$PREVIEW_URL"
setvar FACTORY_BOT_USER "$bot_user"
setvar FACTORY_REF "$FACTORY_REF"

say "Webhook: start a pass when someone files an issue or comments"
default_branch=$(api GET "projects/$fid" | json "d['default_branch']")
trigger=$(api GET "projects/$fid/triggers" | json "next((t['token'] for t in d if t['description'] == 'test-drive webhook'), '')")
if [ -z "$trigger" ] || [ "${#trigger}" -lt 20 ]; then
  trigger=$(api POST "projects/$fid/triggers" --data-urlencode "description=test-drive webhook" | json "d['token']")
fi
# GitLab calls itself: allow requests to 127.0.0.1 from webhooks, and nothing wider.
allow=$(api GET application/settings | json "d.get('outbound_local_requests_whitelist') or []")
if ! echo "$allow" | grep -q "127.0.0.1"; then
  raw=$(echo "$allow" | python3 -c "import ast,sys; print(','.join(ast.literal_eval(sys.stdin.read()) + ['127.0.0.1']))")
  if api PUT application/settings --data-urlencode "outbound_local_requests_allowlist_raw=$raw" >/dev/null; then
    echo "allowed webhooks to call 127.0.0.1"
  else
    echo "warning: could not allow 127.0.0.1. In Admin Area > Settings > Network > Outbound requests, add 127.0.0.1 to the allowlist."
  fi
fi
hook_url="http://127.0.0.1/api/v4/projects/$fid/ref/$default_branch/trigger/pipeline?token=$trigger"
hook=$(api GET "projects/$sid/hooks" | json "next((h['id'] for h in d if '/trigger/pipeline' in h['url']), '')")
if [ -n "$hook" ]; then
  api PUT "projects/$sid/hooks/$hook" --data-urlencode "url=$hook_url" -d issues_events=true -d note_events=true \
    -d push_events=false -d enable_ssl_verification=false >/dev/null
else
  api POST "projects/$sid/hooks" --data-urlencode "url=$hook_url" -d issues_events=true -d note_events=true \
    -d push_events=false -d enable_ssl_verification=false >/dev/null
fi
echo "issues and comments on $SANDBOX_PROJECT now start a pass of $FACTORY_PROJECT"

say "Ready"
cat <<EOF
File an issue:     $GITLAB_URL/$SANDBOX_PROJECT/-/issues/new?issuable_template=Feature
Watch the passes:  $GITLAB_URL/$FACTORY_PROJECT/-/pipelines
Previews:          ${PREVIEW_URL/\{item\}/}

Previews are served on port $PREVIEW_PORT. Open it in the firewall if it is closed,
or put a hostname in front of it and run this again with PREVIEW_URL set.
Previews are public to anyone with the link; they show only the sandbox app.
EOF
