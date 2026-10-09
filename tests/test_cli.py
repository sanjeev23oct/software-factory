import io
import os
import tempfile
import unittest

from tasklite.cli import main


class CliTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.db = os.path.join(self.dir.name, "tasks.json")

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = main(["--db", self.db] + list(argv), out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def test_add_then_list(self):
        self.run_cli("add", "buy milk")
        code, out, _ = self.run_cli("list")
        self.assertEqual(code, 0)
        self.assertEqual(out, "[ ]   1  buy milk\n")

    def test_done_unknown_id_fails(self):
        code, _, err = self.run_cli("done", "9")
        self.assertEqual(code, 1)
        self.assertIn("no task with id 9", err)
