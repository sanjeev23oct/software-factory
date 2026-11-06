#!/bin/sh
# Runs inside the preview container at start (nginx runs every script in
# /docker-entrypoint.d/). Serves each client's project in its own area:
#
#   /<site>/main/     the app as it is on main
#   /<site>/<item>/   each `factory/<item>` branch, so a person at a gate can use the change
#   /<site>/status/   where each request stands, as the factory last wrote it
#
# refreshed every 20 seconds. One file per site in /etc/factory-sites:
#
#   <site>.env        REPO=<clone URL as seen from this container>  TOKEN=<read_repository token>
#   <site>.htpasswd   optional: the site's basic-auth logins. Without it the site is open.
#
#   STATUS_REPO     optional: the factory project, whose `factory-state` branch holds each site's
#                   <site>/status.html (the site's name is the factory pipeline's name)
#   STATUS_TOKEN    a read_repository token for that project
set -u
command -v git >/dev/null || apk add --no-cache git >/dev/null 2>&1 || { echo "preview: could not install git"; exit 0; }
ROOT=${PREVIEW_ROOT:-/usr/share/nginx/html}
SITES=${PREVIEW_SITES:-/etc/factory-sites}
CACHE=${PREVIEW_CACHE:-/var/cache/preview}
CONF=${PREVIEW_CONF:-/etc/nginx/conf.d/default.conf}
mkdir -p "$CACHE"

sites() {
  for env in "$SITES"/*.env; do [ -f "$env" ] && basename "$env" .env; done
}

# One location per site, behind its own logins. The root names no client.
write_conf() {
  {
    echo 'server {'
    echo '  listen 80;'
    echo '  server_name _;'
    echo "  root $ROOT;"
    echo '  location = / { try_files /index.html =404; }'
    for site in $(sites); do
      echo "  location /$site/ {"
      if [ -f "$SITES/$site.htpasswd" ]; then
        echo "    auth_basic \"$site\";"
        echo "    auth_basic_user_file $SITES/$site.htpasswd;"
      fi
      echo '  }'
    done
    echo '  location / { return 404; }'
    echo '}'
  } > "$CONF"
  printf '%s\n' '<!doctype html><meta charset="utf-8"><title>Software factory</title>' \
    '<body style="font:16px system-ui;margin:2rem"><h1>Software factory</h1>' \
    '<p>Each client has their own link. Ask the person who invited you for yours.</p>' > "$ROOT/index.html"
}

# fetch REPO REFSPEC... into the mirror MIRROR, signing in with TOKEN in a header, never in the URL.
fetch() {
  mirror=$1 token=$2 repo=$3; shift 3
  [ -d "$mirror" ] || git init -q --bare "$mirror" || return 1
  auth=$(printf 'oauth2:%s' "$token" | base64 | tr -d '\n')
  GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=http.extraHeader GIT_CONFIG_VALUE_0="Authorization: Basic $auth" \
    git -C "$mirror" fetch -q --prune "$repo" "$@" 2>/tmp/preview-fetch.err \
    || { echo "preview: fetch from $repo failed: $(head -c 300 /tmp/preview-fetch.err)"; return 1; }
}

sync_site() {
  site=$1
  REPO=$(sed -n 's/^REPO=//p' "$SITES/$site.env"); TOKEN=$(sed -n 's/^TOKEN=//p' "$SITES/$site.env")
  mirror="$CACHE/$site.git" out="$ROOT/$site"
  fetch "$mirror" "$TOKEN" "$REPO" '+refs/heads/main:refs/heads/main' '+refs/heads/factory/*:refs/heads/factory/*' || return
  mkdir -p "$out"
  live=""
  for ref in $(git -C "$mirror" for-each-ref --format='%(refname:short)' refs/heads/); do
    name=$(basename "$ref")
    live="$live $name"
    sha=$(git -C "$mirror" rev-parse "$ref")
    [ "$(cat "$out/$name/.sha" 2>/dev/null)" = "$sha" ] && continue
    rm -rf "$out/.next-$name" && mkdir -p "$out/.next-$name"
    git -C "$mirror" archive "$ref" | tar -x -C "$out/.next-$name" && echo "$sha" > "$out/.next-$name/.sha"
    rm -rf "$out/$name" && mv "$out/.next-$name" "$out/$name"
    echo "preview: $site/$ref -> /$site/$name/ at $(echo "$sha" | cut -c1-8)"
  done
  for dir in "$out"/*/; do
    [ -d "$dir" ] || continue
    name=$(basename "$dir")
    case " $live status " in *" $name "*) ;; *) rm -rf "$dir"; echo "preview: removed /$site/$name/" ;; esac
  done
  if [ -n "$status_ok" ] && git -C "$CACHE/status.git" show "factory-state:$site/status.html" > "$out/.status.html" 2>/dev/null; then
    mkdir -p "$out/status" && mv "$out/.status.html" "$out/status/index.html"
  fi
  {
    echo '<!doctype html><meta charset="utf-8"><title>Previews</title><body style="font:16px system-ui;margin:2rem">'
    echo '<h1>Previews</h1>'
    [ -f "$out/status/index.html" ] && echo '<p><a href="status/">Where each request stands</a></p>'
    echo '<ul>'
    for name in $live; do echo "<li><a href=\"$name/\">$name</a></li>"; done
    echo '</ul><p>Each request the factory builds appears here as its branch is pushed.</p>'
  } > "$out/index.html"
}

sync_once() {
  status_ok=""
  if [ -n "${STATUS_REPO:-}" ] && fetch "$CACHE/status.git" "$STATUS_TOKEN" "$STATUS_REPO" '+refs/heads/factory-state:refs/heads/factory-state'; then
    status_ok=1
  fi
  for site in $(sites); do sync_site "$site"; done
}

write_conf
if [ "${PREVIEW_ONCE:-}" ]; then sync_once; else ( while true; do sync_once; sleep 20; done ) & fi
