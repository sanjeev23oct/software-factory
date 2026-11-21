"""Controls every code-writing pipeline has: the security gate, the model for each kind of work,
and checked sections pushed as they pass."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "factory"))
import flow  # noqa: E402

SKILLS = ROOT / "factories" / "skills"


def pipeline(name):
    definition = json.loads((ROOT / "factories" / name / "factory.json").read_text())
    definition["source"].update(project="group/app", repo="owner/app")
    return definition


class SecurityGateTest(unittest.TestCase):
    def test_every_sample_that_writes_code_has_the_gate(self):
        for name in ("ui-app", "backend-api", "spec-driven", "bugfix"):
            with self.subTest(name):
                self.assertEqual([], flow.validate(pipeline(name), SKILLS))
                self.assertIn("security-scan", [s.get("skill") for s in pipeline(name)["stages"]])

    def test_a_code_writing_pipeline_without_it_is_refused(self):
        definition = pipeline("ui-app")
        definition["stages"] = [s for s in definition["stages"] if s.get("skill") != "security-scan"]
        self.assertTrue(any("security gate" in p for p in flow.validate(definition, SKILLS)))

    def test_switching_it_off_does_not_count(self):
        definition = pipeline("backend-api")
        for stage in definition["stages"]:
            if stage.get("skill") == "security-scan":
                stage["enabled"] = False
        self.assertTrue(any("security gate" in p for p in flow.validate(definition, SKILLS)))

    def test_a_pipeline_that_only_reviews_needs_no_gate(self):
        self.assertFalse(any("security gate" in p for p in flow.validate(pipeline("request-review"), SKILLS)))

    def test_the_review_is_after_the_security_gate_and_before_the_person(self):
        ids = [s["id"] for s in pipeline("ui-app")["stages"]]
        self.assertLess(ids.index("verify"), ids.index("security"))
        self.assertLess(ids.index("security"), ids.index("ai-review"))
        self.assertLess(ids.index("check-review"), ids.index("approve-screens"))


class ModelTest(unittest.TestCase):
    def setUp(self):
        p = patch.object(flow, "DEFINITION", {"stages": []})
        p.start()
        self.addCleanup(p.stop)

    def test_defaults_by_kind_of_work(self):
        stages = {s["id"]: s for s in pipeline("ui-app")["stages"]}
        self.assertEqual("opus", flow.model_for(stages["requirements"]))
        self.assertEqual("opus", flow.model_for(stages["tasks"]))
        self.assertEqual("sonnet", flow.model_for(stages["build"], "maker"))
        self.assertEqual("sonnet", flow.model_for(stages["build"], "checker"))
        self.assertEqual("sonnet", flow.model_for(stages["ai-review"]))

    def test_the_pipeline_and_a_stage_can_choose(self):
        flow.DEFINITION["models"] = {"build": "haiku"}
        self.assertEqual("haiku", flow.model_for({"id": "build", "by": "agent", "until": "all-tasks-ticked"}, "maker"))
        self.assertEqual("opus", flow.model_for({"id": "tasks", "by": "agent", "model": "opus"}))

    def test_an_unknown_kind_is_refused(self):
        definition = dict(pipeline("ui-app"), models={"planning": "opus"})
        self.assertTrue(any("unknown kind" in p for p in flow.validate(definition, SKILLS)))


class PushPerSectionTest(unittest.TestCase):
    def test_pushed_on_a_runner_only(self):
        item = {"id": "GL7"}
        pushes = []
        fake_cloud = SimpleNamespace(push_branch=lambda repo, branch, token_env=None: pushes.append(branch) or
                                     SimpleNamespace(returncode=0, stderr=""))
        with patch.dict(sys.modules, {"cloud": fake_cloud}):
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("FACTORY_REPOS_DIR", None)
                flow.push_checked_section(item)
            self.assertEqual([], pushes)
            with patch.dict(os.environ, {"FACTORY_REPOS_DIR": "/tmp/repos"}):
                flow.push_checked_section(item)
        self.assertEqual(["factory/GL7"], pushes)


class SecurityScanTest(unittest.TestCase):
    def test_a_missing_tool_stops_rather_than_passing(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for cmd in (["init", "-q", "-b", "main"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
                subprocess.run(["git"] + cmd, cwd=tmp, check=True)
            (repo / "a.txt").write_text("a\n")
            subprocess.run(["git", "add", "."], cwd=tmp, check=True)
            subprocess.run(["git", "commit", "-qm", "a"], cwd=tmp, check=True)
            git_only = Path(tmp) / "bin"
            git_only.mkdir()
            (git_only / "git").symlink_to(subprocess.run(["which", "git"], capture_output=True, text=True).stdout.strip())
            proc = subprocess.run([sys.executable, str(ROOT / "factory" / "scripts" / "security_scan.py"),
                                   "--repo", tmp, "--base", "main"], capture_output=True, text=True,
                                  env=dict(os.environ, PATH=str(git_only)))
        self.assertEqual(2, proc.returncode)
        self.assertIn("gitleaks is not installed", proc.stdout)

    def test_only_vulnerabilities_the_change_adds_count(self):
        sys.path.insert(0, str(ROOT / "factory" / "scripts"))
        import security_scan
        before = {("npm", "lodash", "", "old")}
        after = before | {("npm", "minimist", "", "new")}
        with patch.object(security_scan, "vulnerable", side_effect=[after, before]), \
                patch.object(security_scan, "run", return_value=SimpleNamespace(returncode=0, stdout="", stderr="")):
            found = security_scan.packages(Path("/repo"), "origin/main", ["pnpm-lock.yaml"])
        self.assertEqual(["vulnerable package npm minimist  new"], found)


if __name__ == "__main__":
    unittest.main()
