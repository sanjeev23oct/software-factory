#!/bin/sh
# Runs inside the preview container at start (nginx runs every script in
# /docker-entrypoint.d/). Serves the sandbox app's `main` at /main/ and each
# `factory/<item>` branch at /<item>/, refreshed every 20 seconds, so a person
# at a gate can use the change the factory just pushed.
#
#   PREVIEW_REPO    clone URL as seen from this container, e.g. http://gitlab/sandbox/test-drive-app.git
#   PREVIEW_TOKEN   a read_repository token for that project
set -u
command -v git >/dev/null || apk add --no-cache git >/dev/null 2>&1 || { echo "preview: could not install git"; exit 0; }
ROOT=${PREVIEW_ROOT:-/usr/share/nginx/html}
MIRROR=${PREVIEW_MIRROR:-/var/cache/preview.git}

sync_once() {
  if [ ! -d "$MIRROR" ]; then
    git init -q --bare "$MIRROR" || return
  fi
  # The token goes in a header through the environment, never into the URL.
  auth=$(printf 'oauth2:%s' "$PREVIEW_TOKEN" | base64 | tr -d '\n')
  GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=http.extraHeader GIT_CONFIG_VALUE_0="Authorization: Basic $auth" git -C "$MIRROR" \
    fetch -q --prune "$PREVIEW_REPO" '+refs/heads/main:refs/heads/main' '+refs/heads/factory/*:refs/heads/factory/*' 2>/tmp/preview-fetch.err \
    || { echo "preview: fetch failed: $(head -c 300 /tmp/preview-fetch.err)"; return; }
  live=""
  for ref in $(git -C "$MIRROR" for-each-ref --format='%(refname:short)' refs/heads/); do
    name=$(basename "$ref")
    live="$live $name"
    sha=$(git -C "$MIRROR" rev-parse "$ref")
    [ "$(cat "$ROOT/$name/.sha" 2>/dev/null)" = "$sha" ] && continue
    rm -rf "$ROOT/.next-$name" && mkdir -p "$ROOT/.next-$name"
    git -C "$MIRROR" archive "$ref" | tar -x -C "$ROOT/.next-$name" && echo "$sha" > "$ROOT/.next-$name/.sha"
    rm -rf "$ROOT/$name" && mv "$ROOT/.next-$name" "$ROOT/$name"
    echo "preview: $ref -> /$name/ at $(echo "$sha" | cut -c1-8)"
  done
  for dir in "$ROOT"/*/; do
    [ -d "$dir" ] || continue
    name=$(basename "$dir")
    case " $live " in *" $name "*) ;; *) rm -rf "$dir"; echo "preview: removed /$name/" ;; esac
  done
  {
    echo '<!doctype html><meta charset="utf-8"><title>Factory previews</title><body style="font:16px system-ui;margin:2rem">'
    echo '<h1>Factory previews</h1><ul>'
    for name in $live; do echo "<li><a href=\"$name/\">$name</a></li>"; done
    echo '</ul><p>Each issue the factory builds appears here as its branch is pushed.</p>'
  } > "$ROOT/index.html"
}

if [ "${PREVIEW_ONCE:-}" ]; then sync_once; else ( while true; do sync_once; sleep 20; done ) & fi
