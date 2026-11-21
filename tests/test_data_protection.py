"""Personal data stays out of what agents read and out of the code; agents read the organisation's knowledge."""

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
sys.path.insert(0, str(ROOT / "factory" / "scripts"))
import factory as core  # noqa: E402
import flow  # noqa: E402
import pii  # noqa: E402
import security_scan  # noqa: E402


class DetectTest(unittest.TestCase):
    def test_finds_each_kind(self):
        text = ("Mail ramesh.k@rssb.org, call +91 98765 43210, switch 100.100.30.53 MAC 3C:52:82:1A:2B:3C, "
                "PAN ABCPE1234F, card 4539 1488 0343 6467")
        kinds = [k for k, _ in pii.find(text)]
        for kind in ("EMAIL", "PHONE", "IP", "MAC", "PAN", "CARD"):
            self.assertIn(kind, kinds)

    def test_leaves_safe_and_ordinary_values(self):
        text = "test@example.com at 192.0.2.10 and 127.0.0.1; totals 1500000, order 98765, card 4111 1111 1111 1111"
        self.assertEqual([], pii.find(text))

    def test_aadhaar_needs_a_valid_checksum(self):
        self.assertEqual([], pii.find("reference 2345 6789 0123"))

    def test_redacts_with_numbered_placeholders_and_counts(self):
        text, counts = pii.redact("a@rssb.org then b@rssb.org then a@rssb.org again")
        self.assertEqual("[EMAIL-1] then [EMAIL-2] then [EMAIL-1] again", text)
        self.assertEqual({"EMAIL": 2}, counts)
        self.assertEqual("2 emails, 1 IP address", pii.describe({"EMAIL": 2, "IP": 1}))

    def test_an_allowed_value_is_kept(self):
        self.assertEqual([], pii.find("write to support@rssb.org", allow=[r"^support@rssb\.org$"]))


class RedactIntakeTest(unittest.TestCase):
    def test_the_issue_is_redacted_before_agents_and_it_is_said(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            (state / "items").mkdir()
            item = {"id": "GL9", "stage": "read-issue", "attempts": {}}
            with patch.object(flow, "STATE", state), patch.object(flow, "DEFINITION", {"stages": []}):
                flow.context_file(item).write_text("Rack locks. Contact ramesh.k@rssb.org, server 100.100.30.53.")
                flow.redact_context(item)
                text = flow.context_file(item).read_text()
            self.assertNotIn("ramesh", text)
            self.assertIn("[EMAIL-1]", text)
            self.assertEqual("1 email, 1 IP address", item["redacted"])
            event = json.loads((state / "events.jsonl").read_text().splitlines()[-1])
            self.assertEqual("personal data redacted", event["event"])
            self.assertIn("Personal data redacted", flow.describe(event))


class AgentSessionTest(unittest.TestCase):
    def run_agent(self, root):
        seen = {}

        def fake_run(cmd, **kwargs):
            seen.update(cmd=cmd, env=kwargs.get("env", {}))
            return SimpleNamespace(stdout=json.dumps({"result": "done", "total_cost_usd": 0.01}), stderr="", returncode=0)
        with patch.object(core, "TARGETS", root / "targets"), patch.object(core, "NAME", "shop"), \
                patch.object(core, "PRESUBMIT", ["presubmit"]), patch.object(core, "EXTRA_TOOLS", []), \
                patch.object(core.subprocess, "run", side_effect=fake_run):
            core.run_headless({"agent": "spec", "prompt": "p", "cwd": str(root)})
        return seen

    def test_secret_and_data_files_are_denied_by_permission_and_hook(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "targets" / "shop").mkdir(parents=True)
            seen = self.run_agent(root)
        settings = json.loads(seen["cmd"][seen["cmd"].index("--settings") + 1])
        self.assertIn("Read(**/.env)", settings["permissions"]["deny"])
        self.assertIn("read_guard.py", settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"])
        self.assertIn("**/.env", json.loads(seen["env"]["FACTORY_DENY_READ"]))
        self.assertNotIn("**/*.sql", core.DENY_READ)   # changesets stay readable; only dumps are denied

    def test_a_target_can_set_its_own_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "targets" / "shop").mkdir(parents=True)
            (root / "targets" / "shop" / "target.json").write_text(json.dumps({"deny_read": ["**/private/**"]}))
            seen = self.run_agent(root)
        self.assertEqual(["**/private/**"], json.loads(seen["env"]["FACTORY_DENY_READ"]))

    def test_the_organisation_knowledge_is_readable_when_there(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "targets" / "shop").mkdir(parents=True)
            self.assertNotIn(str(root / "knowledge"), self.run_agent(root)["cmd"])
            (root / "knowledge").mkdir()
            (root / "knowledge" / "INDEX.md").write_text("# Shared services\n")
            self.assertIn(str(root / "knowledge"), self.run_agent(root)["cmd"])


class ReadGuardTest(unittest.TestCase):
    def guard(self, command, patterns):
        return subprocess.run([sys.executable, str(ROOT / "factory" / "scripts" / "read_guard.py")],
                              input=json.dumps({"tool_input": {"command": command}}), text=True, capture_output=True,
                              env=dict(os.environ, FACTORY_DENY_READ=json.dumps(patterns))).returncode

    def test_blocks_a_command_naming_a_denied_file(self):
        self.assertEqual(2, self.guard("cat backend/.env", ["**/.env"]))
        self.assertEqual(2, self.guard("git show HEAD:config/appsettings.Production.json", ["**/appsettings.Production*.json"]))

    def test_lets_ordinary_commands_through(self):
        self.assertEqual(0, self.guard("dotnet build backend/InfraManagement.slnx", ["**/.env", "**/*.csv"]))


class ChangeScanTest(unittest.TestCase):
    def test_personal_data_in_added_lines_is_found_and_masked(self):
        with tempfile.TemporaryDirectory() as tmp:
            for cmd in (["init", "-q", "-b", "main"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
                subprocess.run(["git"] + cmd, cwd=tmp, check=True)
            (Path(tmp) / "seed.cs").write_text("// owner: old@rssb.org\n")
            subprocess.run(["git", "add", "."], cwd=tmp, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=tmp, check=True)
            (Path(tmp) / "seed.cs").write_text("// owner: old@rssb.org\nvar ip = \"100.100.30.53\";\n")
            subprocess.run(["git", "commit", "-qam", "change"], cwd=tmp, check=True)
            found = security_scan.personal_data(Path(tmp), "HEAD~1", [])
        self.assertEqual(1, len(found))                  # only what the change added
        self.assertIn("ip 10***53 in seed.cs", found[0])
        self.assertNotIn("100.100.30.53", found[0])


if __name__ == "__main__":
    unittest.main()
