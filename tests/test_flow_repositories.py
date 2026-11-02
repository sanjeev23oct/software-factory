"""One issue may change and publish several GitLab repositories."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "factory"))
import factory as core  # noqa: E402
import cloud  # noqa: E402
import flow  # noqa: E402
import open_merge_request  # noqa: E402
import repositories  # noqa: E402


def git(repo, *args):
    proc = subprocess.run(["git"] + list(args), cwd=str(repo), text=True, capture_output=True)
    if proc.returncode:
        raise AssertionError(proc.stderr or proc.stdout)
    return proc.stdout.strip()


def make_repo(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    git(path.parent, "init", "-q", "-b", "main", str(path))
    git(path, "config", "user.name", "Factory Test")
    git(path, "config", "user.email", "factory-test@example.test")
    (path / "README.md").write_text("first\n")
    git(path, "add", "README.md")
    git(path, "commit", "-qm", "first")


class RepositoryFlowTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("KIROCREW_SCRATCH"))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.primary = self.root / "primary"
        self.ui = self.root / "ui"
        make_repo(self.primary)
        make_repo(self.ui)
        self.state = self.root / "state"
        (self.state / "items").mkdir(parents=True)
        for obj, key, value in ((core, "REPO", self.primary), (core, "NAME", "test"),
                                (core, "MAIN", "main"), (core, "WORKTREES", self.root / "worktrees"),
                                (core, "PROTECTED", ()), (flow, "STATE", self.state),
                                (flow, "DEFINITION", {"stages": [
                                    {"id": "build", "by": "agent", "skill": "build-backend"},
                                    {"id": "approve", "by": "human"}], "commit": True})):
            p = patch.object(obj, key, value)
            p.start()
            self.addCleanup(p.stop)
        config = {"repositories": {"ui": {
            "repo": str(self.ui), "main": "main", "host": "gitlab.example.test", "project": "team/ui",
            "presubmit": [sys.executable, "-c", "import sys; sys.exit(0)"],
            "protected": ["secret/"]}}}
        self.repos = repositories.RepositorySet("test", config)
        p = patch.object(flow, "REPOSITORIES", self.repos)
        p.start()
        self.addCleanup(p.stop)
        self.item = {"id": "GL12", "ref": "12", "title": "Add feature", "spec": "specs/12",
                     "stage": "build", "status": "pending", "skip": [], "attempts": {}}

    def test_untouched_repository_needs_no_check_or_request(self):
        self.repos.repos["ui"]["presubmit"] = [sys.executable, "-c", "raise SystemExit(1)"]
        self.assertEqual({}, self.repos.changed(self.item))
        self.assertEqual((True, "no additional repositories changed"),
                         self.repos.verify(self.item, flow.checkout(self.item)))

    def test_finish_commits_both_checkouts_and_runs_joint_check(self):
        primary = flow.checkout(self.item)
        ui = self.repos.checkout(self.item, "ui")
        (primary / "backend.py").write_text("ready = True\n")
        (ui / "ui.py").write_text("ready = True\n")
        flow.finish(self.item)
        self.assertEqual("approve", self.item["stage"])
        self.assertEqual("build: Add feature", git(primary, "log", "-1", "--format=%s"))
        self.assertEqual("build: Add feature", git(ui, "log", "-1", "--format=%s"))
        self.assertEqual(["ui"], list(self.repos.changed(self.item)))
        self.repos.integration = [sys.executable, "-c",
                                  "import os,pathlib; assert pathlib.Path(os.environ['FACTORY_REPO_UI'], 'ui.py').exists()"]
        self.assertTrue(self.repos.verify(self.item, primary)[0])

    def test_agent_receives_only_configured_extra_checkout(self):
        (self.state / "items" / "GL12.context.md").write_text("An issue description\n")
        with patch.object(core, "GUIDE", ROOT / "AGENTS.md"):
            task = flow.agent_task(self.item, {"id": "build", "by": "agent", "skill": "build-backend",
                                              "agent": "builder"})
        ui_checkout = str(self.repos.checkout(self.item, "ui"))
        self.assertEqual([ui_checkout], task["add_dirs"])
        self.assertIn("ui: " + ui_checkout, task["prompt"])
        self.assertNotIn(str(self.ui) + " (guide:", task["prompt"])

    def test_protected_file_in_extra_repo_is_rejected(self):
        flow.checkout(self.item)
        ui = self.repos.checkout(self.item, "ui")
        (ui / "secret").mkdir()
        (ui / "secret" / "token.txt").write_text("do not commit\n")
        with self.assertRaisesRegex(core.FactoryError, "ui:secret/token.txt, which is protected"):
            flow.finish(self.item)
        self.assertFalse(self.repos.committed(self.item, "ui"))

    def test_repo_name_cannot_escape_worktree_root(self):
        config = {"repositories": {"../outside": {}}}
        with self.assertRaisesRegex(core.FactoryError, "invalid additional repository name"):
            repositories.RepositorySet("test", config)

    def test_runner_clones_extra_repo_from_configured_remote(self):
        bare = self.root / "ui-remote.git"
        git(self.root, "init", "-q", "--bare", str(bare))
        git(self.ui, "remote", "add", "origin", str(bare))
        git(self.ui, "push", "-q", "origin", "main")
        config = {"repositories": {"ui": {
            "remote": str(bare), "main": "main", "host": "gitlab.example.test",
            "project": "team/ui", "presubmit": [sys.executable, "-c", "pass"]}}}
        runner = self.root / "runner"
        with patch.dict(os.environ, {"FACTORY_REPOS_DIR": str(runner), "FACTORY_GITLAB_TOKEN": "test-token",
                                      "FACTORY_GIT_TOKEN": ""}):
            cloned = repositories.RepositorySet("test", config)
        self.assertEqual(runner / "test" / "ui", cloned.repos["ui"]["repo"])
        self.assertEqual("first", (cloned.repos["ui"]["repo"] / "README.md").read_text().strip())

    def test_next_runner_pass_restores_extra_branch(self):
        bare = self.root / "ui-remote.git"
        git(self.root, "init", "-q", "--bare", str(bare))
        git(self.ui, "remote", "add", "origin", str(bare))
        git(self.ui, "push", "-q", "origin", "main")
        config = {"repositories": {"ui": {
            "remote": str(bare), "main": "main", "host": "gitlab.example.test",
            "project": "team/ui", "presubmit": [sys.executable, "-c", "pass"]}}}
        with patch.dict(os.environ, {"FACTORY_REPOS_DIR": str(self.root / "pass-one"),
                                      "FACTORY_GITLAB_TOKEN": "test-token", "FACTORY_GIT_TOKEN": ""}):
            first = repositories.RepositorySet("test", config)
            wt = first.checkout(self.item, "ui")
            (wt / "ui.py").write_text("ready = True\n")
            git(wt, "add", "ui.py")
            git(wt, "commit", "-qm", "add ui")
            pushed = cloud.push_branch(first.repos["ui"]["repo"], first.branch(self.item, "ui"),
                                       token_env="FACTORY_GITLAB_TOKEN")
            self.assertEqual(0, pushed.returncode, pushed.stderr)
        with patch.dict(os.environ, {"FACTORY_REPOS_DIR": str(self.root / "pass-two"),
                                      "FACTORY_GITLAB_TOKEN": "test-token", "FACTORY_GIT_TOKEN": ""}), \
                patch.object(core, "WORKTREES", self.root / "pass-two-worktrees"):
            second = repositories.RepositorySet("test", config)
            restored = second.checkout(self.item, "ui")
        self.assertEqual("ready = True", (restored / "ui.py").read_text().strip())


class MergeRequestTest(unittest.TestCase):
    def setUp(self):
        primary_check = patch.object(core, "presubmit", return_value=(True, "primary ok"))
        primary_check.start()
        self.addCleanup(primary_check.stop)
        self.item = {"id": "GL12", "ref": "12", "title": "Add feature"}
        self.stage = {"id": "merge-request", "by": "script", "skill": "open-merge-request",
                      "run": ["python3", "open-primary-mr.py"]}
        self.extra = SimpleNamespace(repos={"ui": {"host": "second.example.test", "project": "team/ui",
                                                        "main": "main", "token_env": "UI_GITLAB_TOKEN"}},
                                     verify=Mock(return_value=(True, "checked")),
                                     changed=Mock(return_value={"ui": Path("/unused/ui")}),
                                     branch=Mock(return_value="factory/test-GL12-ui"))

    def test_one_issue_opens_request_in_each_changed_repo(self):
        results = [SimpleNamespace(returncode=0, stdout="Merge request opened: https://first.example.test/mr/1\n", stderr=""),
                   SimpleNamespace(returncode=0, stdout="Merge request already open: https://second.example.test/mr/2\n", stderr="")]
        definition = {"source": {"type": "gitlab", "host": "first.example.test",
                                 "project": "team/backend", "write": True}}
        with patch.object(flow, "REPOSITORIES", self.extra), patch.object(flow, "DEFINITION", definition), \
                patch.object(flow, "checkout", return_value=Path("/unused/backend")), \
                patch.object(flow, "primary_has_commits", return_value=True), \
                patch.object(flow, "fill", side_effect=lambda item, text: text), \
                patch.object(flow, "post_merge_requests", return_value=(True, "posted")) as post, \
                patch.object(flow.subprocess, "run", side_effect=results) as run:
            ok, output = flow.run_script(self.item, self.stage)
        self.assertTrue(ok, output)
        self.assertIn("ui:", output)
        self.assertEqual(2, run.call_count)
        extra_cmd = run.call_args_list[1].args[0]
        self.assertEqual("second.example.test", extra_cmd[extra_cmd.index("--host") + 1])
        self.assertEqual("https://first.example.test/team/backend/-/issues/12",
                         extra_cmd[extra_cmd.index("--issue-url") + 1])
        self.assertNotIn("--issue", extra_cmd)
        self.assertEqual("UI_GITLAB_TOKEN", extra_cmd[extra_cmd.index("--token-env") + 1])
        self.assertEqual(2, len(self.item["merge_requests"]))
        post.assert_called_once()

    def test_checks_fail_before_any_merge_request(self):
        self.extra.verify.return_value = (False, "ui checks failed")
        with patch.object(flow, "REPOSITORIES", self.extra), \
                patch.object(flow, "checkout", return_value=Path("/unused/backend")), \
                patch.object(flow.subprocess, "run") as run:
            ok, output = flow.run_script(self.item, self.stage)
        self.assertFalse(ok)
        self.assertEqual("ui checks failed", output)
        run.assert_not_called()

    def test_primary_check_fails_before_any_merge_request(self):
        with patch.object(flow, "REPOSITORIES", self.extra), \
                patch.object(core, "presubmit", return_value=(False, "backend checks failed")), \
                patch.object(flow, "checkout", return_value=Path("/unused/backend")), \
                patch.object(flow.subprocess, "run") as run:
            ok, output = flow.run_script(self.item, self.stage)
        self.assertFalse(ok)
        self.assertIn("backend checks failed", output)
        run.assert_not_called()

    def test_only_secondary_repo_changes(self):
        result = SimpleNamespace(returncode=0, stdout="Merge request opened: https://second.example.test/mr/2", stderr="")
        definition = {"source": {"type": "gitlab", "host": "first.example.test",
                                 "project": "team/backend", "write": False}}
        with patch.object(flow, "REPOSITORIES", self.extra), patch.object(flow, "DEFINITION", definition), \
                patch.object(flow, "checkout", return_value=Path("/unused/backend")), \
                patch.object(flow, "primary_has_commits", return_value=False), \
                patch.object(flow, "fill", side_effect=lambda item, text: text), \
                patch.object(flow.subprocess, "run", return_value=result) as run:
            ok, output = flow.run_script(self.item, self.stage)
        self.assertTrue(ok, output)
        self.assertEqual(1, run.call_count)
        self.assertEqual({"ui": "https://second.example.test/mr/2"}, self.item["merge_requests"])

    def test_old_single_repo_stage_runs_one_command(self):
        result = SimpleNamespace(returncode=0, stdout="done", stderr="")
        with patch.object(flow, "REPOSITORIES", None), \
                patch.object(flow, "DEFINITION", {"source": {"type": "gitlab"}}), \
                patch.object(flow, "checkout", return_value=Path("/unused/backend")), \
                patch.object(flow, "fill", side_effect=lambda item, text: text), \
                patch.object(flow.subprocess, "run", return_value=result) as run:
            self.assertEqual((True, "done"), flow.run_script(self.item, self.stage))
        self.assertEqual(1, run.call_count)

    def test_merge_request_note_is_not_posted_twice(self):
        definition = {"source": {"type": "gitlab", "host": "first.example.test",
                                 "project": "team/backend", "write": True}}
        note = [{"text": "<!-- software-factory:merge-requests test GL12 -->"}]
        with patch.object(flow, "DEFINITION", definition), patch.object(core, "NAME", "test"), \
                patch.object(flow, "read_issue", return_value=json.dumps(note)), \
                patch.object(flow.subprocess, "run") as run:
            self.assertEqual((True, "merge-request links already posted"),
                             flow.post_merge_requests(self.item, {"primary": "https://first.example.test/mr/1"}))
        run.assert_not_called()

    def test_extra_request_links_original_issue_without_closing_other_issue(self):
        args = SimpleNamespace(issue=None, issue_url="https://first.example.test/team/backend/-/issues/12",
                               branch="factory/test-GL12-ui", spec=None, repo="/unused/ui")
        body = open_merge_request.description(args, "https://second.example.test/team/ui")
        self.assertIn("Related issue: https://first.example.test/team/backend/-/issues/12", body)
        self.assertNotIn("Closes #12", body)


class GitCredentialTest(unittest.TestCase):
    def test_each_host_uses_its_named_token(self):
        result = SimpleNamespace(returncode=0, stdout="", stderr="")
        with patch.dict(os.environ, {"FIRST_TOKEN": "first-secret", "SECOND_TOKEN": "second-secret"}), \
                patch.object(cloud.subprocess, "run", return_value=result) as run:
            cloud.git(["status"], Path("/unused"), token_env="FIRST_TOKEN")
            self.assertEqual("first-secret", run.call_args.kwargs["env"]["FACTORY_PUSH_TOKEN"])
            cloud.git(["status"], Path("/unused"), token_env="SECOND_TOKEN")
            self.assertEqual("second-secret", run.call_args.kwargs["env"]["FACTORY_PUSH_TOKEN"])
            self.assertNotIn("second-secret", run.call_args.args[0])

    def test_missing_named_token_fails_before_git(self):
        with patch.dict(os.environ, {"MISSING_TEST_TOKEN": ""}), \
                patch.object(cloud.subprocess, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "set MISSING_TEST_TOKEN"):
                cloud.git(["status"], Path("/unused"), token_env="MISSING_TEST_TOKEN")
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
