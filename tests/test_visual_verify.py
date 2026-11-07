"""The visual verifier, tested by planting defects in a screen it has accepted.

A verifier nobody has tested is an opinion. Each planted defect must fail, each
harmless variation must pass, and the same build must give the same report.
The suite needs Node and Chrome; without them it is skipped, not passed.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "factory" / "scripts" / "visual_verify.mjs"
HERE = ROOT / "tests" / "visual"
CHROMES = [os.environ.get("CHROME", ""), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
           "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable"]
READY = shutil.which("node") and any(c and os.path.exists(c) for c in CHROMES) and not os.environ.get("FACTORY_SKIP_VISUAL")

# (name, kind, change, (the region that must fail, the checks that may catch it))
DEFECTS = [
    ("element moved 24px", "css", "#totals { position: relative; left: 24px; top: 24px; }", ("totals", {"geometry", "similarity"})),
    ("accent colour swapped", "css", ":root { --accent: #c2410c; }", ("open-value", {"color"})),
    ("heading font 20% smaller", "css", "h1 { font-size: 22px; }", ("heading", {"geometry", "similarity"})),
    ("component removed", "css", "#totals { display: none; }", ("totals", {"present"})),
    ("label changed", "replace", ("src/render.js", "Open deal value", "Pipeline value"), ("totals", {"text"})),
    ("row wraps to two lines", "css", "#customers td:nth-child(2) { max-width: 90px; }", ("customer-table", {"geometry", "similarity"})),
]
HARMLESS = [
    ("different data in a masked area", "mask", ("data/customers.json", "Maria Lopez", "Mariah Lopes"), None),
    ("sub-pixel shift", "css", "main { transform: translateX(0.4px); }", None),
    ("near-identical page background", "css", ":root { --bg: #f3f4f6; }", None),
]
TABLE_ROWS = [160, 250, 960, 270]   # the customer rows: data that changes, so a contract may mask it


def verify(app, contract, out):
    proc = subprocess.run(["node", str(SCRIPT), "--root", str(app), "--contract", str(contract), "--out", str(out)],
                          capture_output=True, text=True, timeout=120)
    if proc.returncode == 2:
        raise RuntimeError(proc.stderr)
    return proc.returncode, json.loads((out / "report.json").read_text())


@unittest.skipUnless(READY, "needs node and Chrome (set CHROME); FACTORY_SKIP_VISUAL skips it")
class VisualVerifyTest(unittest.TestCase):
    results = []

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="visual-suite-"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)
        defects = [r for r in cls.results if r[1] == "defect"]
        harmless = [r for r in cls.results if r[1] == "harmless"]
        caught = sum(1 for r in defects if r[2])
        alarms = sum(1 for r in harmless if not r[2])
        for name, kind, ok, how in cls.results:
            print("  {:<34} {:<9} {}".format(name, "caught" if kind == "defect" and ok else "MISSED" if kind == "defect"
                                           else "passed" if ok else "ALARM", how), file=sys.stderr)
        if defects and harmless:
            print("\nvisual verifier: caught {}/{} planted defects; {}/{} false alarms".format(
                caught, len(defects), alarms, len(harmless)), file=sys.stderr)

    def build(self, name, kind, change):
        """A copy of the accepted screen with one change, and the contract to check it with."""
        app = self.tmp / name.replace(" ", "-").replace("%", "pc").replace(":", "")
        shutil.copytree(HERE / "crm", app)
        contract = json.loads((HERE / "crm-contract.json").read_text())
        contract["reference"] = str(HERE / contract["reference"])
        if kind == "css":
            with open(app / "styles.css", "a") as f:
                f.write("\n" + change + "\n")
        elif kind in ("replace", "mask"):
            path, old, new = change
            text = (app / path).read_text()
            self.assertIn(old, text, "the change must apply")
            (app / path).write_text(text.replace(old, new))
            if kind == "mask":
                contract["mask"] = [TABLE_ROWS]
        contract_path = app.parent / (app.name + "-contract.json")
        contract_path.write_text(json.dumps(contract))
        # VISUAL_EVIDENCE_DIR keeps each case's compare.png and report.json, e.g. for a write-up.
        keep = os.environ.get("VISUAL_EVIDENCE_DIR")
        return app, contract_path, (Path(keep) if keep else app.parent) / (app.name + "-evidence")

    def test_the_accepted_screen_passes(self):
        code, report = verify(HERE / "crm", HERE / "crm-contract.json", self.tmp / "accepted")
        self.assertEqual(0, code, report["failures"])
        self.assertTrue(all(r["similarity"] == 1 and r["iou"] == 1 for r in report["regions"]))

    def test_every_planted_defect_fails(self):
        for name, kind, change, (region, checks) in DEFECTS:
            with self.subTest(name):
                code, report = verify(*self.build(name, kind, change))
                failed = {f["region"]: f["failed"] for f in report["failures"]}
                by = sorted(checks & set(failed.get(region, [])))
                self.results.append((name, "defect", code == 1 and bool(by), "{}: {}".format(region, ", ".join(by) or "not caught")))
                self.assertEqual(1, code, "{} passed the verifier".format(name))
                self.assertTrue(by, "{}: expected {} to fail one of {}, got {}".format(name, region, sorted(checks), failed))

    def test_harmless_variation_passes(self):
        for name, kind, change, _ in HARMLESS:
            with self.subTest(name):
                code, report = verify(*self.build(name, kind, change))
                self.results.append((name, "harmless", code == 0, ", ".join(f["region"] for f in report["failures"]) or "no region failed"))
                self.assertEqual(0, code, "{} raised a false alarm: {}".format(name, report["failures"]))

    def test_the_same_build_gives_the_same_report(self):
        _, first = verify(HERE / "crm", HERE / "crm-contract.json", self.tmp / "run-1")
        _, second = verify(HERE / "crm", HERE / "crm-contract.json", self.tmp / "run-2")
        self.assertEqual(first, second)
        self.assertEqual((self.tmp / "run-1" / "actual.png").read_bytes(), (self.tmp / "run-2" / "actual.png").read_bytes())


if __name__ == "__main__":
    unittest.main()
