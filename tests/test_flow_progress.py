"""Progress comments on the issue, open approval for a sandbox, and the preview link."""

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


def record(item, stage, event, detail=""):
    return {"ts": "2026-11-05T10:15:00Z", "item": item, "stage": stage, "event": event, "detail": detail, "cost_usd": None}


class ProgressTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.state = Path(temp.name)
        (self.state / "items").mkdir()
        self.definition = {"source": {"type": "gitlab", "host": "gitlab.example.test", "project": "sandbox/app",
                                      "approvers": ["*"], "progress": True},
                           "stages": [{"id": "build", "by": "agent", "skill": "build-tasks"}]}
        for key, value in (("STATE", self.state), ("DEFINITION", self.definition)):
            p = patch.object(flow, key, value)
            p.start()
            self.addCleanup(p.stop)
        self.item = {"id": "GL5", "ref": "5", "title": "Search", "spec": "specs/5", "stage": "build",
                     "status": "pending", "skip": [], "attempts": {"build": 1}, "source": "gitlab"}
        flow.item_path("GL5").write_text(json.dumps(self.item))

    def write_events(self, *records):
        with open(self.state / "events.jsonl", "a") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

    def report(self):
        captured = []

        def fake_run(cmd, **kwargs):
            captured.append(Path(cmd[cmd.index("--file") + 1]).read_text())
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        with patch.object(flow.subprocess, "run", side_effect=fake_run):
            flow.cmd_report(None)
        return captured

    def test_any_commenter_may_approve_when_approvers_is_star(self):
        self.assertTrue(flow.may_approve("Someone-New"))
        item = dict(self.item, waiting_since="2026-11-05T10:00:00")
        notes = [{"who": "exec1", "when": "2026-11-05T10:05:00Z", "text": "/approve"}]
        self.assertEqual(("exec1", []), flow.approval(item, notes))

    def test_named_approvers_still_exclude_others(self):
        self.definition["source"]["approvers"] = ["lead"]
        item = dict(self.item, waiting_since="2026-11-05T10:00:00")
        notes = [{"who": "exec1", "when": "2026-11-05T10:05:00Z", "text": "/approve"}]
        self.assertIsNone(flow.approval(item, notes))
        self.assertFalse(flow.may_approve("exec1"))

    def test_report_posts_new_steps_once(self):
        self.write_events(record("GL5", "read-issue", "started", "Search"),
                          record("GL5", "build", "moved on"),
                          record("GL5", "build", "checker session failed the section", "grep found 1, expected 2"))
        first = self.report()
        self.assertEqual(1, len(first))
        self.assertIn("Picked up the issue", first[0])
        self.assertIn("checker failed the section", first[0])
        self.assertIn("grep found 1, expected 2", first[0])
        self.assertNotIn("moved on", first[0])
        self.assertIn("attempt 2 of 3", first[0])
        self.assertEqual([], self.report())
        self.write_events(record("GL5", "build", "checker session passed the section", "session abc"))
        second = self.report()
        self.assertEqual(1, len(second))
        self.assertNotIn("Picked up", second[0])

    def test_report_skips_items_with_only_bookkeeping(self):
        self.write_events(record("GL5", "build", "moved on"), record("GL5", "build", "agent task handed out"))
        self.assertEqual([], self.report())
        self.assertEqual(2, json.loads(flow.item_path("GL5").read_text())["reported"])

    def test_report_is_off_unless_the_pipeline_asks(self):
        del self.definition["source"]["progress"]
        self.write_events(record("GL5", "read-issue", "started", "Search"))
        self.assertEqual([], self.report())

    def test_failed_post_is_retried_next_pass(self):
        self.write_events(record("GL5", "read-issue", "started", "Search"))
        with patch.object(flow.subprocess, "run", return_value=SimpleNamespace(returncode=1, stdout="", stderr="403")):
            flow.cmd_report(None)
        self.assertEqual(1, len(self.report()))

    def test_preview_link_reaches_report_and_gate(self):
        self.write_events(record("GL5", "preview", "script passed", "Try it: https://preview.example.test/GL5/  (ready soon)"))
        self.assertEqual("https://preview.example.test/GL5/", flow.latest_preview(self.item))
        self.assertIn("**Try it:** https://preview.example.test/GL5/", self.report()[0])


class PreviewLinkTest(unittest.TestCase):
    script = str(ROOT / "factory" / "scripts" / "preview_link.py")

    def run_script(self, env):
        return subprocess.run([sys.executable, self.script, "--item", "GL5"], text=True, capture_output=True,
                              env=dict(os.environ, **env))

    def test_fills_the_template(self):
        out = self.run_script({"FACTORY_PREVIEW_URL": "https://p.example.test/{item}/"})
        self.assertEqual(0, out.returncode)
        self.assertIn("Try it: https://p.example.test/GL5/", out.stdout)

    def test_passes_without_a_preview_server(self):
        out = self.run_script({"FACTORY_PREVIEW_URL": ""})
        self.assertEqual(0, out.returncode)
        self.assertNotIn("Try it", out.stdout)


class OwnCommentTest(unittest.TestCase):
    def test_pass_started_by_the_factory_itself_does_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            payload = Path(temp) / "payload.json"
            payload.write_text(json.dumps({"object_kind": "note", "user": {"username": "factory-bot"}}))
            out = subprocess.run(["sh", str(ROOT / "factory" / "scripts" / "ci_tick.sh")], cwd=temp, text=True,
                                 capture_output=True, env=dict(os.environ, TRIGGER_PAYLOAD=str(payload),
                                                               FACTORY_BOT_USER="factory-bot"))
        self.assertEqual(0, out.returncode)
        self.assertIn("started by the factory's own comment", out.stdout)


if __name__ == "__main__":
    unittest.main()
