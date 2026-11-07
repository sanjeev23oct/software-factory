"""The visual verification loop in the pipeline: references in, evidence committed, baselines out."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "factory"))
sys.path.insert(0, str(ROOT / "factory" / "scripts"))
import factory as core  # noqa: E402
import flow  # noqa: E402
import read_issue  # noqa: E402
import visual_checks  # noqa: E402


def git(repo, *args):
    proc = subprocess.run(["git"] + list(args), cwd=str(repo), text=True, capture_output=True)
    if proc.returncode:
        raise AssertionError(proc.stderr or proc.stdout)
    return proc.stdout.strip()


class AttachedImagesTest(unittest.TestCase):
    def test_finds_each_attached_screenshot_once(self):
        body = ("Make it look like this ![dash](/uploads/0123456789abcdef0123/Customers.png)\n"
                "again ![dash](/uploads/0123456789abcdef0123/Customers.png) and ![m](/uploads/fedcba9876543210ffff/mobile.JPG)\n"
                "but not a link [log](/uploads/0123456789abcdef0123/log.txt) or ![remote](https://example.test/x.png)")
        self.assertEqual([("0123456789abcdef0123", "Customers.png"), ("fedcba9876543210ffff", "mobile.JPG")],
                         read_issue.attached_images(body))

    def test_no_description_means_no_images(self):
        self.assertEqual([], read_issue.attached_images(None))


class VisualChecksTest(unittest.TestCase):
    def test_references_first_then_baselines_the_request_did_not_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, spec = Path(tmp), Path(tmp) / "specs" / "3-x"
            (spec / "reference").mkdir(parents=True)
            (repo / "baselines").mkdir()
            for path in (spec / "reference" / "dashboard.json", repo / "baselines" / "dashboard.json",
                         repo / "baselines" / "settings.json"):
                path.write_text("{}")
            self.assertEqual([("dashboard", "reference"), ("settings", "baseline")],
                             [(screen, kind) for screen, _, kind in visual_checks.contracts(spec, repo)])

    def test_nothing_to_check_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run([sys.executable, str(ROOT / "factory" / "scripts" / "visual_checks.py"),
                                   "--spec", str(Path(tmp) / "specs" / "1-x"), "--repo", tmp], capture_output=True, text=True)
        self.assertEqual(0, proc.returncode)
        self.assertIn("nothing to check", proc.stdout)


class VisualFlowTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.repo = self.root / "repo"
        git(self.root, "init", "-q", "-b", "main", str(self.repo))
        git(self.repo, "config", "user.name", "Factory Test")
        git(self.repo, "config", "user.email", "factory-test@example.test")
        (self.repo / "index.html").write_text("<h1>Hi</h1>\n")
        git(self.repo, "add", "index.html")
        git(self.repo, "commit", "-qm", "first")
        self.state = self.root / "state"
        (self.state / "items").mkdir(parents=True)
        self.definition = {"source": {"type": "gitlab", "host": "gitlab.example.test", "project": "clients/app",
                                      "approvers": ["*"]},
                           "stages": [{"id": "visual-verify", "by": "script", "skill": "visual-verify", "commits": True,
                                       "error_code": 2, "on_fail": "visual-verify", "run": []},
                                      {"id": "approve-screens", "by": "human", "baselines": True},
                                      {"id": "merge-request", "by": "script", "run": ["true"]}]}
        for obj, key, value in ((core, "REPO", self.repo), (core, "NAME", "test"), (core, "MAIN", "main"),
                                (core, "WORKTREES", self.root / "worktrees"), (core, "PROTECTED", ()), (core, "PRESUBMIT", ["true"]),
                                (flow, "STATE", self.state), (flow, "DEFINITION", self.definition),
                                (flow, "REPOSITORIES", None)):
            p = patch.object(obj, key, value)
            p.start()
            self.addCleanup(p.stop)
        self.item = {"id": "GL3", "ref": "3", "title": "Dashboard", "spec": "specs/3-dashboard", "source": "gitlab",
                     "stage": "visual-verify", "status": "pending", "skip": [], "attempts": {}}
        flow.item_path("GL3").write_text(json.dumps(self.item))

    def stage(self, script):
        return dict(self.definition["stages"][0], run=[sys.executable, "-c", script])

    def evidence(self, wt):
        """What visual_checks.py leaves for one screen: the contract, the screenshot and the report."""
        spec = wt / self.item["spec"]
        (spec / "reference").mkdir(parents=True)
        (spec / "evidence" / "visual" / "dashboard").mkdir(parents=True)
        (spec / "reference" / "dashboard.json").write_text(json.dumps({
            "reference": "dashboard.png", "viewport": [1280, 800],
            "regions": [{"name": "totals", "testid": "totals", "box": [0, 0, 10, 10], "iou": 0.6, "similarity": False}]}))
        (spec / "evidence" / "visual" / "dashboard" / "actual.png").write_bytes(b"\x89PNG built")
        (spec / "evidence" / "visual" / "dashboard" / "compare.png").write_bytes(b"\x89PNG compare")
        (spec / "evidence" / "visual" / "dashboard" / "report.json").write_text(json.dumps({
            "pass": True, "regions": [{"name": "totals", "box": [8, 16, 960, 104]}]}))

    def test_a_committing_script_keeps_its_evidence_with_the_work(self):
        wt = flow.checkout(self.item)
        ok, output = flow.run_script(self.item, self.stage(
            "from pathlib import Path; Path('specs/3-dashboard/evidence/visual/x').mkdir(parents=True);"
            "Path('specs/3-dashboard/evidence/visual/x/report.json').write_text('{}'); print('visual-verify: PASS')"))
        self.assertTrue(ok, output)
        self.assertIn("specs/3-dashboard/evidence/visual/x/report.json", git(wt, "show", "--stat", "--name-only", "HEAD"))
        self.assertEqual("", git(wt, "status", "--porcelain"))

    def test_commit_paths_keeps_a_reference_whatever_the_spec_folder_is_called(self):
        # git's exclusion pathspecs (":!issue_context.md") made `git add` stage nothing for some folder names,
        # such as specs/2-build-..., so the intake's screenshot was never committed and the next stage tripped on it.
        wt = flow.checkout(self.item)
        (wt / "issue_context.md").write_text("the requirement\n")
        for spec in ("specs/2-build-this-customer-dashboard", "specs/2-x"):
            (wt / spec / "reference").mkdir(parents=True)
            (wt / spec / "reference" / "customers.png").write_bytes(b"\x89PNG reference")
            flow.commit_paths(wt, [spec + "/reference"], "reference: " + spec)
            self.assertIn(spec + "/reference/customers.png", git(wt, "show", "--name-only", "HEAD"))
        self.assertEqual("?? issue_context.md", git(wt, "status", "--porcelain"))

    def test_a_check_that_could_not_run_stops_for_a_person(self):
        with patch.object(flow, "run_script", return_value=(None, "visual-verify: could not check: no Chrome")):
            flow.step(self.item)
        self.assertEqual("blocked", self.item["status"])
        self.assertEqual("visual-verify", self.item["stage"])

    def test_the_could_not_check_code_is_reported_as_none(self):
        flow.checkout(self.item)
        ok, _ = flow.run_script(self.item, self.stage("import sys; print('no Chrome'); sys.exit(2)"))
        self.assertIsNone(ok)
        ok, _ = flow.run_script(self.item, self.stage("import sys; sys.exit(1)"))
        self.assertIs(False, ok)

    def test_approving_the_screens_saves_strict_baselines(self):
        wt = flow.checkout(self.item)
        self.evidence(wt)
        git(wt, "add", "-A")
        git(wt, "commit", "-qm", "evidence")
        self.item.update(stage="approve-screens", status="waiting", waiting_since="2026-11-07T10:00:00")
        flow.approve(self.item, by="client")
        baseline = json.loads((wt / "baselines" / "dashboard.json").read_text())
        self.assertEqual("dashboard.png", baseline["reference"])
        self.assertEqual([8, 16, 960, 104], baseline["regions"][0]["box"])
        self.assertEqual((0.95, 0.98), (baseline["regions"][0]["iou"], baseline["regions"][0]["similarity"]))
        self.assertEqual(b"\x89PNG built", (wt / "baselines" / "dashboard.png").read_bytes())
        self.assertIn("baselines: Dashboard", git(wt, "log", "--oneline", "-1"))
        self.assertEqual("merge-request", self.item["stage"])

    def test_the_screens_gate_shows_reference_vs_built(self):
        self.evidence(flow.checkout(self.item))
        images = flow.visual_evidence(self.item)
        self.assertEqual(1, len(images))
        self.assertIn("![dashboard reference vs built](https://gitlab.example.test/clients/app/-/raw/factory/GL3/"
                      "specs/3-dashboard/evidence/visual/dashboard/compare.png)", images[0])
        self.assertIn("passed", images[0])

    def test_a_reply_without_approving_is_a_possible_verifier_miss_once(self):
        self.item.update(stage="approve-screens", status="waiting", waiting_since="2026-11-07T10:00:00")
        notes = [{"who": "client", "when": "2026-11-07T10:05:00Z", "text": "The cards should be in one row"},
                 {"who": "client", "when": "2026-11-07T09:00:00Z", "text": "from before the gate opened"},
                 {"who": "root", "when": "2026-11-07T10:06:00Z", "text": "**Factory progress** <!-- software-factory:progress GL3 -->"}]
        with patch.dict(os.environ, {"FACTORY_BOT_USER": "root"}):
            flow.record_misses(self.item, notes)
            flow.record_misses(self.item, notes)
        misses = [json.loads(line) for line in (self.state / "events.jsonl").read_text().splitlines()
                  if json.loads(line)["event"] == "verifier miss"]
        self.assertEqual(1, len(misses))
        self.assertIn("one row", misses[0]["detail"])


class SamplePipelinesTest(unittest.TestCase):
    def test_the_ui_pipelines_with_visual_verification_are_sound(self):
        for name in ("test-drive", "ui-app"):
            with self.subTest(name):
                definition = json.loads((ROOT / "factories" / name / "factory.json").read_text())
                definition["source"].update(project="group/app", repo="owner/app")
                self.assertEqual([], flow.validate(definition, ROOT / "factories" / "skills"))
                ids = [s["id"] for s in definition["stages"]]
                self.assertLess(ids.index("verify"), ids.index("visual-verify"))
                self.assertLess(ids.index("visual-verify"), ids.index("approve-screens"))


if __name__ == "__main__":
    unittest.main()
