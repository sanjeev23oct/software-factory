#!/usr/bin/env python3
"""The visual-verify stage: check every reference screen, and every approved baseline, against what was built.

    visual_checks.py --spec CHECKOUT/specs/3-dashboard --repo CHECKOUT

For each contract in <spec>/reference/*.json it runs visual_verify.mjs and writes the evidence to
<spec>/evidence/visual/<screen>/. Screens approved earlier have a baseline in <repo>/baselines/; those
this request did not set out to change are checked strictly too, so a change elsewhere cannot quietly
break them. Exit 0 when every screen passes or there is nothing to check, 1 when a screen fails (the
build redoes it), 2 when the check could not run at all (a person looks).
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

VERIFY = Path(__file__).resolve().parent / "visual_verify.mjs"


def contracts(spec, repo):
    """[(screen, contract path, kind)] to check: the request's references, then the other baselines."""
    references = sorted((spec / "reference").glob("*.json"))
    named = {path.stem for path in references}
    baselines = sorted(p for p in (repo / "baselines").glob("*.json") if p.stem not in named)
    return [(p.stem, p, "reference") for p in references] + [(p.stem, p, "baseline") for p in baselines]


def check(screen, contract, kind, spec, repo):
    out = spec / "evidence" / "visual" / ("baseline-" + screen if kind == "baseline" else screen)
    proc = subprocess.run(["node", str(VERIFY), "--root", str(repo), "--contract", str(contract), "--out", str(out)],
                          capture_output=True, text=True, timeout=300)
    if proc.returncode == 2:
        return 2, "{} `{}`: could not check: {}".format(kind, screen, (proc.stderr or proc.stdout).strip()[:400])
    report = json.loads((out / "report.json").read_text())
    if report["pass"]:
        return 0, "{} `{}`: PASS ({} regions)".format(kind, screen, len(report["regions"]))
    lines = ["{} `{}`: FAIL; see {}/compare.png".format(kind, screen, out.relative_to(repo))]
    for region in report["regions"]:
        if region["pass"]:
            continue
        failed = [name for name, ok in region["checks"].items() if not ok]
        detail = []
        if "present" in failed:
            detail.append("not on the page, or not visible ({})".format(region["selector"]))
        if "geometry" in failed:
            detail.append("box {} vs reference {} (IoU {} < {})".format(region["box"], region["reference_box"],
                                                                        region["iou"], region["thresholds"]["iou"]))
        if "text" in failed:
            detail.append("missing text: " + ", ".join(repr(t) for t in region["missing_text"]))
        if "color" in failed:
            detail.append("; ".join("{} {} vs {} (ΔE {})".format(c["property"], c["actual"], c["expected"], c["delta_e"])
                                    for c in region["colors"] if c["delta_e"] > region["thresholds"]["delta_e"]))
        if "similarity" in failed:
            detail.append("looks different: similarity {} < {}".format(region["similarity"], region["thresholds"]["similarity"]))
        lines.append("- region `{}`: {}".format(region["name"], "; ".join(detail)))
    return 1, "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--spec", required=True)
    p.add_argument("--repo", required=True)
    args = p.parse_args()
    spec, repo = Path(args.spec).resolve(), Path(args.repo).resolve()
    todo = contracts(spec, repo)
    if not todo:
        print("visual-verify: no reference screens or baselines; nothing to check")
        return 0
    if not shutil.which("node"):
        print("visual-verify: could not check: node is not installed on this runner")
        return 2
    worst, lines = 0, []
    for screen, contract, kind in todo:
        code, line = check(screen, contract, kind, spec, repo)
        worst = max(worst, code)
        lines.append(line)
    print("\n".join(lines))
    print("visual-verify: {}".format({0: "PASS", 1: "FAIL", 2: "could not check"}[worst]))
    return worst


if __name__ == "__main__":
    sys.exit(main())
