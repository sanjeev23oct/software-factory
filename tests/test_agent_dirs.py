"""An agent may read its pipeline's AGENTS.md and skills, wherever the pipeline folder lives."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "factory"))
import factory as core  # noqa: E402


class AgentDirsTest(unittest.TestCase):
    def test_the_pipeline_folder_is_readable_by_the_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            targets = Path(tmp) / "factory-pipelines" / "targets"
            (targets / "shop").mkdir(parents=True)
            seen = {}

            def fake_run(cmd, **kwargs):
                seen["cmd"] = cmd
                return SimpleNamespace(stdout=json.dumps({"result": "done", "total_cost_usd": 0.01}), stderr="", returncode=0)
            with patch.object(core, "TARGETS", targets), patch.object(core, "NAME", "shop"), \
                    patch.object(core, "PRESUBMIT", ["presubmit"]), patch.object(core, "EXTRA_TOOLS", []), \
                    patch.object(core.subprocess, "run", side_effect=fake_run):
                core.run_headless({"agent": "spec", "prompt": "p", "cwd": tmp})
            dirs = [seen["cmd"][i + 1] for i, part in enumerate(seen["cmd"]) if part == "--add-dir"]
            self.assertIn(str(targets / "shop"), dirs)


if __name__ == "__main__":
    unittest.main()
