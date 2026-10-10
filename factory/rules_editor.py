#!/usr/bin/env python3
"""A local page for editing a target's process rules.

    python3 factory/rules_editor.py [--port 8787] [--no-open]

It serves on 127.0.0.1 only. The page reads and writes
targets/<name>/process.json, and can try unsaved rules against a real merge
request without posting anything.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOME / "factory" / "scripts"))
import check_mr_process as process  # noqa: E402

TARGETS = HOME / "targets"
PAGE = HOME / "factory" / "rules_editor.html"


def target_dir(name):
    path = TARGETS / name
    if "/" in name or name.startswith(".") or not (path / "process.json").exists():
        raise ValueError("no such target with process rules: {}".format(name))
    return path


def folders(repo):
    """Top two levels of tracked folders, as suggestions for path fields."""
    out = subprocess.run(["git", "ls-tree", "-d", "-r", "--name-only", "HEAD"], cwd=str(repo), text=True, capture_output=True).stdout
    return sorted({p + "/" for p in out.splitlines() if p.count("/") <= 2})[:400]


def try_rules(name, cfg, ref):
    """Run cfg against merge request `ref` in a throwaway checkout. Nothing is posted or saved."""
    home = target_dir(name)
    repo = Path(json.loads((home / "target.json").read_text())["repo"])
    source = json.loads((home / "factory.json").read_text())["source"]
    reader = [sys.executable, str(HOME / "factory" / "scripts" / "read_mr.py"), "--project", source["project"]]
    reader += ["--host", source["host"]] if source.get("host") else []
    with tempfile.TemporaryDirectory() as tmp:
        context = Path(tmp) / "context.md"
        proc = subprocess.run(reader + ["--ref", str(ref), "--out", str(context)], text=True, capture_output=True)
        if proc.returncode:
            raise ValueError((proc.stderr or proc.stdout).strip()[:300])
        info = json.loads(proc.stdout.strip().splitlines()[-1])
        fetch = subprocess.run(["git", "fetch", "-q", "origin", info["branch"], info["target"]], cwd=str(repo), text=True, capture_output=True)
        if fetch.returncode:
            raise ValueError("could not fetch the branch: " + fetch.stderr.strip()[:200])
        checkout = Path(tmp) / "checkout"
        subprocess.run(["git", "worktree", "add", "-q", "--detach", str(checkout), info["sha"]], cwd=str(repo), check=True)
        try:
            rows = process.run(checkout, "origin/" + info["target"], cfg, context.read_text())
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(checkout)], cwd=str(repo))
    return {"title": info["title"], "rows": rows}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, payload, status=200, kind="application/json"):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", kind + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        try:
            if url.path == "/":
                self.send(PAGE.read_bytes(), kind="text/html")
            elif url.path == "/api/state":
                names = sorted(p.parent.name for p in TARGETS.glob("*/process.json"))
                self.send({"targets": names, "checks": process.CHECKS, "rule_types": process.RULE_TYPES})
            elif url.path == "/api/config":
                home = target_dir(parse_qs(url.query)["target"][0])
                repo = Path(json.loads((home / "target.json").read_text())["repo"])
                self.send({"config": json.loads((home / "process.json").read_text()), "folders": folders(repo), "repo": str(repo)})
            else:
                self.send({"error": "not found"}, 404)
        except (ValueError, KeyError) as e:
            self.send({"error": str(e)}, 400)

    def do_POST(self):
        # Only this page may change anything: same host, and a header a cross-site form cannot set.
        if self.headers.get("X-Factory-Editor") != "1" or self.headers.get("Host", "").split(":")[0] not in ("127.0.0.1", "localhost"):
            return self.send({"error": "refused"}, 403)
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            problems = process.validate(data["config"])
            if problems:
                return self.send({"problems": problems})
            if self.path == "/api/save":
                path = target_dir(data["target"]) / "process.json"
                shutil.copy(path, path.with_suffix(".json.bak"))
                path.write_text(json.dumps(data["config"], indent=2) + "\n")
                self.send({"saved": True})
            elif self.path == "/api/try":
                self.send(try_rules(data["target"], data["config"], data["ref"]))
            else:
                self.send({"error": "not found"}, 404)
        except (ValueError, KeyError, subprocess.CalledProcessError) as e:
            self.send({"error": str(e)}, 400)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--port", type=int, default=8787)
    p.add_argument("--no-open", action="store_true")
    args = p.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = "http://127.0.0.1:{}/".format(args.port)
    print("Rules editor at {}  (Ctrl-C to stop)".format(url))
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
