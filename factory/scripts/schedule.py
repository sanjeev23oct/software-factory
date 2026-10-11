#!/usr/bin/env python3
"""Install, remove, or inspect the scheduled job that runs the factory unattended (macOS).

    schedule.py install --every 10 [TARGET ...]    run a pass every 10 minutes; no targets = every route that is switched on
    schedule.py status
    schedule.py remove

The job is a per-user launchd agent. It runs only while you are logged in, and
it runs factory/scripts/tick.sh, which does nothing when there is no new work.
"""

import argparse
import os
import plistlib
import subprocess
import sys
from pathlib import Path

LABEL = "com.software-factory.tick"
PLIST = Path.home() / "Library" / "LaunchAgents" / (LABEL + ".plist")
HOME = Path(__file__).resolve().parent.parent.parent
DOMAIN = "gui/{}".format(os.getuid())


def launchctl(*args):
    return subprocess.run(["launchctl"] + list(args), text=True, capture_output=True)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    install = sub.add_parser("install")
    install.add_argument("--every", type=int, default=10, help="minutes between passes")
    install.add_argument("targets", nargs="*", help="default: every factory switched to pick up work automatically")
    sub.add_parser("status")
    sub.add_parser("remove")
    args = p.parse_args()

    if args.command == "install":
        logs = HOME / ".factory" / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        launchctl("bootout", DOMAIN + "/" + LABEL)
        PLIST.parent.mkdir(parents=True, exist_ok=True)
        with open(PLIST, "wb") as f:
            plistlib.dump({
                "Label": LABEL,
                "ProgramArguments": ["/bin/sh", str(HOME / "factory" / "scripts" / "tick.sh")] + args.targets,
                "StartInterval": args.every * 60,
                "RunAtLoad": False,
                "StandardOutPath": str(logs / "launchd.log"),
                "StandardErrorPath": str(logs / "launchd.log"),
            }, f)
        result = launchctl("bootstrap", DOMAIN, str(PLIST))
        if result.returncode:
            sys.exit("schedule: could not load the job: {}".format(result.stderr.strip()))
        print("Installed. Every {} minutes it checks: {}".format(
            args.every, ", ".join(args.targets) or "every route that is switched on"))
        print("Log: {}".format(logs / "tick.log"))
    elif args.command == "remove":
        launchctl("bootout", DOMAIN + "/" + LABEL)
        if PLIST.exists():
            PLIST.unlink()
        print("Removed.")
    else:
        result = launchctl("print", DOMAIN + "/" + LABEL)
        if result.returncode:
            print("Not installed.")
            return
        field = lambda name: next((line.split("=", 1)[1].strip() for line in result.stdout.splitlines()
                                   if line.strip().startswith(name + " =")), "")
        with open(PLIST, "rb") as f:
            job = plistlib.load(f)
        print("Running in the background: yes")
        print("Checks for new work every {} minutes".format(job["StartInterval"] // 60))
        print("Routes: {}".format(", ".join(job["ProgramArguments"][2:]) or "every route that is switched on"))
        print("Passes since it was installed: {}".format(field("runs") or "0"))
        print("Right now: {}".format("a pass is running" if field("state") == "running" else "idle until the next pass"))


if __name__ == "__main__":
    main()
