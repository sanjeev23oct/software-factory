#!/usr/bin/env python3
"""Local pages for editing a factory without touching its files.

    python3 factory/editor.py [--port 8787] [--no-open]

  /        the route: where work comes from, the stops, the gates, the limits
  /skills  the skills a route's agents follow: add, import, edit
  /rules   the process rules a merge request is checked against
  /activity   what the factory is doing now, and the gates waiting for a person

It serves on 127.0.0.1 only. It reads and writes targets/<name>/factory.json
and process.json, keeping the previous version of each as a .bak file.
"""

import argparse
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOME / "factory" / "scripts"))
sys.path.insert(0, str(HOME / "factory"))
import check_mr_process as process  # noqa: E402
import flow  # noqa: E402

TARGETS = HOME / "targets"
PAGES = {"/": HOME / "factory" / "editor_route.html", "/rules": HOME / "factory" / "editor_rules.html",
         "/skills": HOME / "factory" / "editor_skills.html",
         "/activity": HOME / "factory" / "editor_activity.html"}
JOB = "com.software-factory.tick"
# flow keeps the current factory in module state, so only one request may use it at a time.
FLOW = threading.Lock()


def scheduler():
    """Is the background job installed, how often does it run, and when did it last pass?"""
    plist = Path.home() / "Library" / "LaunchAgents" / (JOB + ".plist")
    installed = subprocess.run(["launchctl", "print", "gui/{}/{}".format(os.getuid(), JOB)], capture_output=True).returncode == 0
    every = None
    if plist.exists():
        with open(plist, "rb") as f:
            every = plistlib.load(f).get("StartInterval", 0) // 60
    log, last = HOME / ".factory" / "logs" / "tick.log", None
    if log.exists():
        stamps = re.findall(r"^== (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)", log.read_text(), re.M)
        last = stamps[-1] if stamps else None
    return {"installed": installed, "every": every, "last_pass": last, "running": (HOME / ".factory" / "tick.lock").exists()}


def activity():
    """Every item in every factory: where it is on its route, and what a person must decide."""
    items = []
    with FLOW:
        for path in sorted(TARGETS.glob("*/factory.json")):
            name = path.parent.name
            try:
                flow.setup(name)
            except flow.core.FactoryError:
                continue
            events = {}
            log = flow.STATE / "events.jsonl"
            for line in log.read_text().splitlines() if log.exists() else []:
                record = json.loads(line)
                events.setdefault(record["item"], []).append(record)
            for item in flow.all_items():
                route = flow.stages(item)
                order = [s["id"] for s in route]
                at = order.index(item["stage"]) if item["stage"] in order else 0
                track = [{"id": s["id"], "by": s["by"], "state": "done" if i < at or item["status"] == "done" else "now" if i == at else "todo"}
                         for i, s in enumerate(route)]
                if route[at].get("checker") and item["status"] == "pending":
                    # Say whose turn it is: the maker's session or the checker's.
                    track[at]["role"] = "checker" if item.get("phase") == "check" else "maker"
                waiting = None
                if item["status"] == "waiting":
                    # What the person is approving: whatever the agents wrote since the previous gate.
                    documents, wt = [], flow.checkout(item)
                    for stage in reversed(route[:at]):
                        if stage["by"] == "human":
                            break
                        for produced in stage.get("produces", []):
                            doc = wt / flow.fill(item, produced)
                            if doc.exists():
                                documents.insert(0, {"name": doc.name, "text": doc.read_text()[:20000]})
                    optional = []
                    for stage in route[at + 1:]:
                        if not stage.get("optional"):
                            break
                        optional.append(stage["id"])
                    waiting = {"gate": item["stage"], "documents": documents, "optional": optional}
                mine = events.get(item["id"], [])
                link = next((m.group(0) for e in reversed(mine) for m in [re.search(r"https://\S+", e.get("detail") or "")] if m), None)
                items.append({"factory": name, "id": item["id"], "title": item["title"], "status": item["status"], "stage": item["stage"],
                              "track": track, "waiting": waiting, "link": link,
                              "updated": mine[-1]["ts"] if mine else "", "cost": sum(e.get("cost_usd") or 0 for e in mine),
                              "events": [{"ts": e["ts"], "stage": e["stage"], "event": e["event"]} for e in mine[-5:]]})
    items.sort(key=lambda i: i["updated"], reverse=True)
    return {"scheduler": scheduler(), "items": items}


def approve(data):
    with FLOW:
        flow.setup(data["target"])
        flow.cmd_approve(argparse.Namespace(item=data["item"], skip=data.get("skip") or None))

LIBRARY = HOME / "factories"


def route_dir(name):
    path = TARGETS / name
    if "/" in name or name.startswith(".") or not (path / "factory.json").exists():
        raise ValueError("no such factory: {}".format(name))
    return path


def about(skill_dir):
    """The one-line description from a skill's front matter."""
    path = skill_dir / "SKILL.md"
    for line in path.read_text().splitlines() if path.exists() else []:
        if line.startswith("description:"):
            return line.split(":", 1)[1].strip()
    return ""


def library(home, definition):
    """Stops a person can add: every stop used by a sample factory, plus the ones this factory already has."""
    stops, seen = [], {s["id"] for s in definition["stages"]}
    for path in sorted(LIBRARY.glob("*/factory.json")):
        for stage in json.loads(path.read_text())["stages"]:
            if path.parent.name == "blank" or stage["id"] in seen or stage.get("intake") or stage["by"] == "human":
                continue
            seen.add(stage["id"])
            stage = dict(stage, enabled=True)
            stops.append({"stage": stage, "about": about(LIBRARY / "skills" / stage.get("skill", ""))})
    return stops


def read_skill(path):
    """A SKILL.md as its parts: the front matter fields the editor shows, and the instructions."""
    text = path.read_text()
    meta, body = {}, text
    if text.startswith("---"):
        _, front, body = text.split("---", 2)
        for line in front.splitlines():
            key, _, value = line.partition(":")
            if value:
                meta[key.strip()] = value.strip()
    return {"name": path.parent.name, "description": meta.get("description", ""), "applies_to": meta.get("applies_to", ""),
            "body": body.strip()}


def skills_of(name):
    """Everything the Skills page shows for one route."""
    home = route_dir(name)
    definition = json.loads((home / "factory.json").read_text())
    used = {}
    for stage in definition["stages"]:
        for skill in (stage.get("skill"), (stage.get("checker") or {}).get("skill")):
            if skill:
                used.setdefault(skill, []).append(stage["id"])
    mine = []
    for path in sorted((home / "skills").glob("*/SKILL.md")):
        entry = read_skill(path)
        entry["used_by"] = used.get(entry["name"], [])
        entry["maker"] = entry["name"].startswith("build-") and entry["name"] != "build-tasks"
        mine.append(entry)
    have = {s["name"] for s in mine}
    repo = Path(json.loads((home / "target.json").read_text())["repo"])
    brief = lambda folder: [{"name": p.parent.name, "description": read_skill(p)["description"]}
                            for p in sorted(folder.glob("*/SKILL.md")) if p.parent.name not in have]
    return {"skills": mine, "library": brief(LIBRARY / "skills"), "repo": brief(repo / ".claude" / "skills"), "repo_path": str(repo)}


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")


def save_skill(data):
    home, name = route_dir(data["target"]), slug(data.get("name", ""))
    if not name:
        raise ValueError("give the skill a name")
    if not data.get("description", "").strip():
        raise ValueError("say in one line what the skill is for")
    if not data.get("body", "").strip():
        raise ValueError("write the instructions the agent should follow")
    folder = home / "skills" / name
    folder.mkdir(parents=True, exist_ok=True)
    globs = ", ".join(g.strip() for g in data.get("applies_to", "").split(",") if g.strip())
    front = "---\nname: {}\ndescription: {}\n".format(name, " ".join(data["description"].split()))
    front += "applies_to: {}\n".format(globs) if (globs or name.startswith("build-")) else ""
    (folder / "SKILL.md").write_text(front + "---\n" + data["body"].strip() + "\n")
    return name


def add_skill(data):
    home, name = route_dir(data["target"]), data["name"]
    source = LIBRARY / "skills" if data.get("source") == "library" else Path(json.loads((home / "target.json").read_text())["repo"]) / ".claude" / "skills"
    if "/" in name or not (source / name / "SKILL.md").exists():
        raise ValueError("no such skill to add: {}".format(name))
    if (home / "skills" / name).exists():
        raise ValueError("this route already has a skill called {}".format(name))
    shutil.copytree(source / name, home / "skills" / name)
    return name


def remove_skill(data):
    home, name = route_dir(data["target"]), data["name"]
    used = next((s for s in skills_of(data["target"])["skills"] if s["name"] == name), None)
    if not used:
        raise ValueError("no such skill: {}".format(name))
    if used["used_by"]:
        raise ValueError("{} is used by the {} stop; remove it from the route first".format(name, ", ".join(used["used_by"])))
    shutil.rmtree(home / "skills" / name)


def samples():
    out = []
    for path in sorted(LIBRARY.glob("*/factory.json")):
        d = json.loads(path.read_text())
        live = [s for s in d["stages"] if s.get("enabled", True)]
        out.append({"name": path.parent.name, "description": d["description"], "source": d["source"]["type"],
                    "example": path.parent.name != "blank",
                    "stops": len(live), "gates": [s["id"].replace("approve-", "") for s in live if s["by"] == "human"]})
    return sorted(out, key=lambda s: s["example"])  # the blank route first


def create(data):
    """Add a repository: clone it if asked, then start its factory from a sample."""
    name = "".join(c if c.isalnum() or c == "-" else "-" for c in data.get("name", "").strip().lower()).strip("-")
    if not name:
        raise ValueError("give the factory a name")
    repo = Path(data.get("repo", "").strip()).expanduser()
    if not str(repo) or str(repo) == ".":
        raise ValueError("say which folder the repository is in")
    if not (repo / ".git").exists():
        url = data.get("clone_url", "").strip()
        if not url:
            raise ValueError("{} is not a git repository. Give a clone address to fetch it there.".format(repo))
        if repo.exists() and any(repo.iterdir()):
            raise ValueError("{} exists and is not empty, so nothing was cloned into it".format(repo))
        proc = subprocess.run(["git", "clone", "-q", url, str(repo)], text=True, capture_output=True,
                              env=dict(__import__("os").environ, GIT_TERMINAL_PROMPT="0"))
        if proc.returncode:
            raise ValueError("could not clone: " + proc.stderr.strip()[-300:])
    try:
        flow.cmd_init(argparse.Namespace(name=name, sample=data.get("sample", ""), repo=str(repo)))
    except flow.core.FactoryError as e:
        raise ValueError(str(e))
    return name


def tools_of(home):
    """The extra programs agents may run, as plain names: Bash(node:*) is shown as node."""
    allowed = json.loads((home / "target.json").read_text()).get("allowed_tools", [])
    return ", ".join(m.group(1) for a in allowed for m in [re.fullmatch(r"Bash\((.+?):\*\)", a)] if m)


def save_route(name, definition, guide=None, presubmit=None, tools=None):
    home = route_dir(name)
    for stage in definition.get("stages", []):
        skill = stage.get("skill")
        if skill and not (home / "skills" / skill).exists() and (LIBRARY / "skills" / skill).exists():
            shutil.copytree(LIBRARY / "skills" / skill, home / "skills" / skill)
    for stage in definition.get("stages", []):
        # A stop built by a maker and a checker needs the checker's skill too.
        checker = (stage.get("checker") or {}).get("skill")
        if checker and not (home / "skills" / checker).exists() and (LIBRARY / "skills" / checker).exists():
            shutil.copytree(LIBRARY / "skills" / checker, home / "skills" / checker)
    problems = flow.validate(definition, home / "skills")
    if problems:
        return problems
    path = home / "factory.json"
    shutil.copy(path, path.with_suffix(".json.bak"))
    path.write_text(json.dumps(definition, indent=2) + "\n")
    if guide is not None:
        (home / "AGENTS.md").write_text(guide.rstrip() + "\n")
    if presubmit is not None:
        (home / "presubmit").write_text(presubmit.rstrip() + "\n")
        (home / "presubmit").chmod(0o755)
    if tools is not None:
        target = json.loads((home / "target.json").read_text())
        target["allowed_tools"] = ["Bash({}:*)".format(t) for t in re.findall(r"[\w./-]+", tools)]
        (home / "target.json").write_text(json.dumps(target, indent=2) + "\n")
    return []


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
            if url.path in PAGES:
                self.send(PAGES[url.path].read_bytes(), kind="text/html")
            elif url.path == "/api/routes":
                self.send({"targets": sorted(p.parent.name for p in TARGETS.glob("*/factory.json"))})
            elif url.path == "/api/route":
                home = route_dir(parse_qs(url.query)["target"][0])
                definition = json.loads((home / "factory.json").read_text())
                skills = {p.parent.name: about(p.parent) for p in sorted((home / "skills").glob("*/SKILL.md"))}
                read = lambda f: (home / f).read_text() if (home / f).exists() else ""
                self.send({"definition": definition, "skills": skills, "library": library(home, definition),
                           "has_rules": (home / "process.json").exists(), "guide": read("AGENTS.md"),
                           "presubmit": read("presubmit"), "tools": tools_of(home), "repo": json.loads(read("target.json") or "{}").get("repo", "")})
            elif url.path == "/api/skills":
                self.send(skills_of(parse_qs(url.query)["target"][0]))
            elif url.path == "/api/activity":
                self.send(activity())
            elif url.path == "/api/samples":
                self.send({"samples": samples()})
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
            if self.path == "/api/route/save":
                problems = save_route(data["target"], data["definition"], data.get("guide"), data.get("presubmit"), data.get("tools"))
                return self.send({"problems": problems} if problems else {"saved": True})
            if self.path == "/api/route/create":
                return self.send({"created": create(data)})
            if self.path == "/api/skills/save":
                return self.send({"saved": save_skill(data)})
            if self.path == "/api/skills/add":
                return self.send({"added": add_skill(data)})
            if self.path == "/api/skills/remove":
                remove_skill(data)
                return self.send({"removed": True})
            if self.path == "/api/approve":
                approve(data)
                return self.send({"approved": True})
            if self.path == "/api/pass":
                # Ask the background job to run now instead of waiting for its next turn.
                done = subprocess.run(["launchctl", "kickstart", "gui/{}/{}".format(os.getuid(), JOB)], capture_output=True, text=True)
                return self.send({"started": done.returncode == 0, "error": done.stderr.strip() or None})
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
        except (ValueError, KeyError, subprocess.CalledProcessError, flow.core.FactoryError) as e:
            self.send({"error": str(e)}, 400)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--port", type=int, default=8787)
    p.add_argument("--no-open", action="store_true")
    args = p.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = "http://127.0.0.1:{}/".format(args.port)
    print("Factory editor at {}  (Ctrl-C to stop)".format(url))
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
