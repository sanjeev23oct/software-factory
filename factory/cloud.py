#!/usr/bin/env python3
"""What the factory needs to run on a CI runner instead of a laptop.

A runner starts empty and forgets everything when the job ends, so each pass
restores what it needs and saves what it changed:

    cloud.py state-pull     clone the factory's progress (the `factory-state` branch) into FACTORY_STATE_DIR
    cloud.py state-push     commit and push it back

Repositories are cloned on demand by factory.use_target() when FACTORY_REPOS_DIR
is set, and flow.py `publish` pushes each item's `factory/*` branch, so the next
pass can carry on where this one stopped.

Git signs in with FACTORY_GIT_TOKEN (or FACTORY_GITLAB_TOKEN), handed to git
through an askpass helper so it never appears on a command line or in a URL.
With neither set, git uses whatever login the machine already has.

    FACTORY_STATE_DIR      where progress lives during the pass
    FACTORY_STATE_REMOTE   the repository that keeps it (default: this CI project)
    FACTORY_STATE_BRANCH   default `factory-state`
"""

import atexit
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

STATE_BRANCH = os.environ.get("FACTORY_STATE_BRANCH", "factory-state")
# Worktrees are rebuilt from the pushed branches, and logs belong to the CI job.
STATE_IGNORE = "*/worktrees/\nlogs/\ntick.lock\n"
_ENV = None


def token():
    return os.environ.get("FACTORY_GIT_TOKEN") or os.environ.get("FACTORY_GITLAB_TOKEN")


def git_env():
    """The environment for a git command that may need to sign in."""
    global _ENV
    if _ENV is None:
        _ENV = dict(os.environ, GIT_TERMINAL_PROMPT="0")
        if token():
            folder = tempfile.mkdtemp(prefix="factory-askpass-")
            atexit.register(shutil.rmtree, folder, True)
            helper = Path(folder) / "askpass"
            helper.write_text('#!/bin/sh\ncase "$1" in Username*) echo oauth2 ;; *) echo "$FACTORY_PUSH_TOKEN" ;; esac\n')
            helper.chmod(0o700)
            _ENV.update(GIT_ASKPASS=str(helper), FACTORY_PUSH_TOKEN=token())
    return _ENV


def git(args, cwd, check=True):
    proc = subprocess.run(["git", "-c", "credential.helper="] + args if token() else ["git"] + args,
                          cwd=str(cwd), text=True, capture_output=True, env=git_env())
    if check and proc.returncode != 0:
        out = (proc.stderr or proc.stdout).strip()
        raise RuntimeError("git {} failed: {}".format(args[0], out.replace(token() or "\0", "***")[:600]))
    return proc


def ensure_clone(path, remote, main):
    """Clone a target's repository with its `factory/*` branches, unless this pass already has it.

    Only on first clone: fetching into a branch that a worktree has checked out is refused."""
    path = Path(path)
    if (path / ".git").exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    git(["clone", "-q", "--branch", main, remote, str(path)], cwd=path.parent)
    git(["fetch", "-q", "origin", "+refs/heads/factory/*:refs/heads/factory/*"], cwd=path)


def push_branch(repo, branch):
    if not branch.startswith("factory/"):
        raise RuntimeError("refusing to push `{}`; only factory/* branches are pushed".format(branch))
    return git(["push", "-q", "origin", "{0}:refs/heads/{0}".format(branch)], cwd=repo, check=False)


def state_remote():
    remote = os.environ.get("FACTORY_STATE_REMOTE")
    if not remote and os.environ.get("CI_PROJECT_PATH"):
        remote = "{}/{}.git".format(os.environ.get("CI_SERVER_URL", "https://gitlab.com"), os.environ["CI_PROJECT_PATH"])
    if not remote:
        sys.exit("cloud: set FACTORY_STATE_REMOTE to the repository that keeps the factory's progress")
    return remote


def state_dir():
    folder = os.environ.get("FACTORY_STATE_DIR")
    if not folder:
        sys.exit("cloud: set FACTORY_STATE_DIR")
    return Path(folder)


def state_pull():
    folder, remote = state_dir(), state_remote()
    if (folder / ".git").exists():
        git(["pull", "-q", "--ff-only", "origin", STATE_BRANCH], cwd=folder)
        return print("state: updated from {}".format(STATE_BRANCH))
    folder.mkdir(parents=True, exist_ok=True)
    has = git(["ls-remote", "--heads", remote, STATE_BRANCH], cwd=folder).stdout.strip()
    if has:
        git(["clone", "-q", "--branch", STATE_BRANCH, "--single-branch", remote, "."], cwd=folder)
        return print("state: restored from {}".format(STATE_BRANCH))
    git(["init", "-q"], cwd=folder)
    git(["checkout", "-q", "-b", STATE_BRANCH], cwd=folder)
    git(["remote", "add", "origin", remote], cwd=folder)
    print("state: none yet; {} will be created".format(STATE_BRANCH))


def state_push():
    folder = state_dir()
    (folder / ".gitignore").write_text(STATE_IGNORE)
    git(["add", "-A"], cwd=folder)
    if not git(["status", "--porcelain"], cwd=folder).stdout.strip():
        return print("state: nothing changed")
    who = ["-c", "user.name=software factory", "-c", "user.email=factory@localhost"]
    git(who + ["commit", "-q", "-m", "factory pass {}".format(os.environ.get("CI_PIPELINE_ID", ""))], cwd=folder)
    git(["push", "-q", "origin", STATE_BRANCH], cwd=folder)
    print("state: saved to {}".format(STATE_BRANCH))


if __name__ == "__main__":
    commands = {"state-pull": state_pull, "state-push": state_push}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        sys.exit(__doc__)
    try:
        commands[sys.argv[1]]()
    except RuntimeError as e:
        sys.exit("cloud: {}".format(e))
