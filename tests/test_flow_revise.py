"""A reply at a gate that is not `approve` sends the document back to the agent that wrote it."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "factory"))
import flow  # noqa: E402

GATE_OPENED = "2026-11-10T11:37:00"


def note(who, when, text):
    return {"who": who, "when": when, "text": text}


class RevisionTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.state, self.wt = root / "state", root / "checkout"
        (self.state / "items").mkdir(parents=True)
        (self.wt / "specs" / "1").mkdir(parents=True)
        (self.wt / "specs" / "1" / "requirements.md").write_text("# Requirements\n")
        self.definition = {
            "source": {"type": "gitlab", "host": "gitlab.example.test", "project": "clients/app", "approvers": ["*"]},
            "stages": [{"id": "read-issue", "by": "script", "intake": True},
                       {"id": "requirements", "by": "agent", "produces": ["{spec}/requirements.md"]},
                       {"id": "visual-spec", "by": "agent", "produces": ["{spec}/visual-spec.md"]},
                       {"id": "approve-requirements", "by": "human"},
                       {"id": "tasks", "by": "agent", "produces": ["{spec}/tasks.md"]},
                       {"id": "build", "by": "agent", "until": "all-tasks-ticked"},
                       {"id": "approve-screens", "by": "human", "baselines": True}]}
        self.posted = []
        for key, value in (("STATE", self.state), ("DEFINITION", self.definition),
                           ("checkout", lambda item: self.wt), ("post_note", self.post)):
            p = patch.object(flow, key, value)
            p.start()
            self.addCleanup(p.stop)
        self.item = {"id": "GL1", "ref": "1", "title": "Coffee", "spec": "specs/1", "stage": "approve-requirements",
                     "status": "waiting", "waiting_since": GATE_OPENED, "notified": "approve-requirements",
                     "skip": [], "attempts": {"requirements": 1}, "source": "gitlab"}
        self.save(self.item)

    def post(self, item, body, name):
        self.posted.append(body)
        return True, ""

    def save(self, item):
        flow.item_path(item["id"]).write_text(json.dumps(item))

    def gates(self, notes, approve=None):
        with patch.object(flow, "read_issue", return_value=json.dumps(notes)), \
                patch.object(flow, "approve", approve or (lambda item, skip, by=None: None)):
            flow.cmd_gates(None)
        return flow.load("GL1")

    def test_a_reply_sends_the_requirements_back_with_it(self):
        item = self.gates([note("vikram.virk", "2026-11-10T11:39:52Z", "4. Editable/deletable? - yes\n5. Several tasters")])
        self.assertEqual(("requirements", "pending"), (item["stage"], item["status"]))
        self.assertIn("5. Several tasters", item["revision"])
        self.assertEqual(0, item["attempts"]["requirements"])
        self.assertNotIn("notified", item)        # the gate notice goes out again with the revised document
        self.assertNotIn("waiting_since", item)
        self.assertIn("Revising requirements.md", self.posted[0])

    def test_approve_still_approves(self):
        approved = []
        self.gates([note("vikram.virk", "2026-11-10T11:40:00Z", "approve")],
                   approve=lambda item, skip, by=None: approved.append(by))
        self.assertEqual(["vikram.virk"], approved)

    def test_the_factorys_own_and_older_comments_are_not_requests(self):
        notes = [note("root", "2026-11-10T11:38:00Z", "**Factory progress** <!-- software-factory:progress GL1 -->"),
                 note("vikram.virk", "2026-11-10T11:30:00Z", "written before the gate opened"),
                 note("bot", "2026-11-10T11:40:00Z", "a comment from the factory's own account")]
        with patch.dict("os.environ", {"FACTORY_BOT_USER": "bot"}):
            item = self.gates(notes)
        self.assertEqual("approve-requirements", item["stage"])
        self.assertEqual([], self.posted)

    def test_each_reply_is_acted_on_once(self):
        reply = note("vikram.virk", "2026-11-10T11:39:52Z", "Several tasters")
        item = self.gates([reply])
        # Back at the gate with the revised requirements: the same reply must not send it round again.
        item.update(stage="approve-requirements", status="waiting", waiting_since=GATE_OPENED, notified="approve-requirements")
        self.save(item)
        item = self.gates([reply])
        self.assertEqual("approve-requirements", item["stage"])
        self.assertEqual(1, item["revisions"])

    def test_a_stage_that_was_skipped_is_passed_over(self):
        self.assertEqual("requirements", flow.revise_target(self.item, self.definition["stages"][3]))

    def test_no_revision_once_code_is_built(self):
        self.assertIsNone(flow.revise_target(self.item, self.definition["stages"][6]))

    def test_a_gate_may_name_the_stage_to_revise(self):
        self.assertEqual("tasks", flow.revise_target(self.item, {"id": "approve-requirements", "revise": "tasks"}))

    def test_too_many_rounds_hand_it_to_a_person(self):
        self.item["revisions"] = flow.REVISION_LIMIT
        self.save(self.item)
        item = self.gates([note("vikram.virk", "2026-11-10T11:39:52Z", "and another change")])
        self.assertEqual("approve-requirements", item["stage"])
        self.assertIn("A maintainer will pick it up", self.posted[0])

    def test_the_agent_gets_the_changes_until_it_finishes(self):
        item = self.gates([note("vikram.virk", "2026-11-10T11:39:52Z", "Several tasters")])
        with patch.object(flow, "agent_task", return_value={"stage": "requirements"}):
            self.assertEqual({"stage": "requirements"}, flow.step(item))
        self.assertIn("Several tasters", (self.wt / flow.FEEDBACK).read_text())


if __name__ == "__main__":
    unittest.main()
