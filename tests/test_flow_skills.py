"""A repository's own skills, such as a team's shared library installed into `.claude/skills`, can build tasks."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "factory"))
import factory as core  # noqa: E402
import flow  # noqa: E402


def skill(folder, name, description):
    (folder / name).mkdir(parents=True)
    (folder / name / "SKILL.md").write_text("---\nname: {}\ndescription: {}\n---\n# {}\n".format(name, description, name))


class RepositorySkillsTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.pipeline, self.repo = root / "targets" / "shop" / "skills", root / "checkout"
        skill(self.pipeline, "build-tests", "the pipeline's test writer")
        skill(self.pipeline, "build-tasks", "the maker itself, never named by a task")
        skill(self.repo / ".claude" / "skills", "build-api-controller", "one thin controller")
        skill(self.repo / ".claude" / "skills", "build-tests", "the repository's own test writer")
        skill(self.repo / ".claude" / "skills", "deploy-uat", "not a maker skill")
        for key, value in (("TARGETS", root / "targets"), ("NAME", "shop")):
            p = patch.object(core, key, value)
            p.start()
            self.addCleanup(p.stop)

    def test_the_plan_is_offered_the_repositorys_build_skills(self):
        rows = "\n".join(flow.maker_skills(self.repo))
        self.assertIn("/build-api-controller`: one thin controller", rows)
        self.assertNotIn("deploy-uat", rows)
        self.assertNotIn("/build-tasks", rows)

    def test_the_pipelines_skill_wins_a_name_clash(self):
        rows = "\n".join(flow.maker_skills(self.repo))
        self.assertIn("the pipeline's test writer", rows)
        self.assertNotIn("the repository's own test writer", rows)

    def test_without_a_checkout_only_the_pipelines_skills(self):
        self.assertEqual(["/build-tests"], [r.split("`")[1] for r in flow.maker_skills()])


if __name__ == "__main__":
    unittest.main()
