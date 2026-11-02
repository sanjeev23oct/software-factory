"""Additional repositories that one factory work item may change."""

import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

import factory as core


NAME = re.compile(r"^[a-z][a-z0-9_-]*$")
ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")


class RepositorySet:
    def __init__(self, target, config):
        self.target = target
        self.repos = {}
        self.integration = config.get("integration")
        if self.integration is not None and (not isinstance(self.integration, list) or
                                             not self.integration or
                                             not all(isinstance(p, str) and p for p in self.integration)):
            raise core.FactoryError("target integration must be a nonempty command list")
        entries = config.get("repositories", {})
        if not isinstance(entries, dict):
            raise core.FactoryError("target repositories must map names to repository settings")
        env_names = set()
        for name, entry in entries.items():
            if not isinstance(name, str) or not NAME.fullmatch(name) or name == "primary":
                raise core.FactoryError("invalid additional repository name: {}".format(name))
            if not isinstance(entry, dict):
                raise core.FactoryError("repository {} needs settings".format(name))
            for key in ("host", "project", "presubmit"):
                if not entry.get(key):
                    raise core.FactoryError("repository {} needs {}".format(name, key))
            if not all(isinstance(entry[key], str) and entry[key] for key in ("host", "project")):
                raise core.FactoryError("repository {} host and project must be text".format(name))
            if "://" in entry["host"] or "/" in entry["host"]:
                raise core.FactoryError("repository {} host must be a domain name".format(name))
            command = entry["presubmit"]
            if not isinstance(command, list) or not all(isinstance(p, str) and p for p in command):
                raise core.FactoryError("repository {} presubmit must be a command list".format(name))
            token_env = entry.get("token_env")
            if token_env and (not isinstance(token_env, str) or not ENV_NAME.fullmatch(token_env)):
                raise core.FactoryError("repository {} token_env must name a CI variable".format(name))
            token_env = token_env or "FACTORY_GITLAB_TOKEN"
            env_name = name.upper().replace("-", "_")
            if env_name in env_names:
                raise core.FactoryError("repository names must have distinct environment names")
            env_names.add(env_name)
            remote = entry.get("remote")
            if remote is not None and not isinstance(remote, str):
                raise core.FactoryError("repository {} remote must be a URL".format(name))
            if not isinstance(entry.get("main", "main"), str) or not entry.get("main", "main"):
                raise core.FactoryError("repository {} main must name a branch".format(name))
            if remote and remote.startswith(("http://", "https://")) and urlsplit(remote).username:
                raise core.FactoryError("repository {} remote must not contain credentials".format(name))
            for field in ("protected", "allowed_tools"):
                value = entry.get(field, [])
                if not isinstance(value, list) or not all(isinstance(p, str) for p in value):
                    raise core.FactoryError("repository {} {} must be a list of text".format(name, field))
            if os.environ.get("FACTORY_REPOS_DIR"):
                if not remote:
                    raise core.FactoryError("repository {} needs remote on a CI runner".format(name))
                repo = Path(os.environ["FACTORY_REPOS_DIR"]) / target / name
                import cloud
                try:
                    cloud.ensure_clone(repo, remote, entry.get("main", "main"), token_env=token_env)
                except RuntimeError as error:
                    raise core.FactoryError(str(error))
            else:
                if not isinstance(entry.get("repo"), str) or not entry["repo"]:
                    raise core.FactoryError("repository {} needs a local repo path".format(name))
                repo = Path(entry["repo"])
            if not (repo / ".git").exists():
                raise core.FactoryError("repository {} points at {}, which is not a git checkout".format(name, repo))
            self.repos[name] = dict(entry, repo=repo, main=entry.get("main", "main"), token_env=token_env)

    def branch(self, item, name):
        return "factory/{}-{}-{}".format(self.target, item["id"], name)

    def checkout(self, item, name):
        entry = self.repos[name]
        repo = entry["repo"]
        wt = core.WORKTREES / "{}--{}".format(item["id"], name)
        if not wt.exists():
            wt.parent.mkdir(parents=True, exist_ok=True)
            branch = self.branch(item, name)
            exists = core.sh(["git", "rev-parse", "--verify", "-q", branch], cwd=repo, check=False).returncode == 0
            cmd = ["git", "worktree", "add", str(wt)] + ([branch] if exists else ["-b", branch, entry["main"]])
            core.sh(cmd, cwd=repo)
        return wt

    def checkouts(self, item):
        return {name: self.checkout(item, name) for name in self.repos}

    def changed(self, item):
        """Additional branches with accepted commits or pending file changes."""
        result = {}
        for name in self.repos:
            wt = self.checkout(item, name)
            if self.committed(item, name) or core.changed_paths(wt):
                result[name] = wt
        return result

    def committed(self, item, name):
        entry = self.repos[name]
        wt = self.checkout(item, name)
        count = core.sh(["git", "rev-list", "--count", "{}..{}".format(entry["main"], self.branch(item, name))],
                        cwd=wt).stdout.strip()
        return int(count) > 0

    def verify(self, item, primary):
        changed = self.changed(item)
        if not changed:
            return True, "no additional repositories changed"
        output = []
        paths = dict(primary=str(primary))
        paths.update({name: str(wt) for name, wt in self.checkouts(item).items()})
        env = dict(os.environ)
        env.update({"FACTORY_REPO_{}".format(name.upper().replace("-", "_")): path
                    for name, path in paths.items()})
        for name, wt in changed.items():
            try:
                proc = subprocess.run(self.repos[name]["presubmit"], cwd=str(wt), env=env,
                                      text=True, capture_output=True)
            except OSError as error:
                return False, "{} presubmit could not start: {}".format(name, error)
            output.append("{} presubmit: {}\n{}".format(name, proc.returncode,
                                                         (proc.stdout + proc.stderr).strip()[-1500:]))
            if proc.returncode:
                return False, "\n".join(output)
        if self.integration:
            try:
                proc = subprocess.run(self.integration, cwd=str(primary), env=env,
                                      text=True, capture_output=True)
            except OSError as error:
                return False, "integration check could not start: {}".format(error)
            output.append("integration: {}\n{}".format(proc.returncode, (proc.stdout + proc.stderr).strip()[-1500:]))
            if proc.returncode:
                return False, "\n".join(output)
        return True, "\n".join(output)
