import os
import tempfile
import unittest

from tasklite.store import Store, TaskNotFound


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path = os.path.join(self.dir.name, "tasks.json")

    def test_add_assigns_increasing_ids(self):
        store = Store(self.path)
        self.assertEqual(store.add("a")["id"], 1)
        self.assertEqual(store.add("b")["id"], 2)

    def test_save_and_reload(self):
        store = Store(self.path)
        store.add("a")
        store.save()
        self.assertEqual(Store(self.path).tasks[0]["title"], "a")

    def test_complete_marks_done(self):
        store = Store(self.path)
        store.add("a")
        store.complete(1)
        self.assertTrue(store.tasks[0]["done"])

    def test_remove_unknown_raises(self):
        store = Store(self.path)
        with self.assertRaises(TaskNotFound):
            store.remove(7)

    def test_complete_unknown_raises(self):
        store = Store(self.path)
        store.add("a")
        with self.assertRaises(TaskNotFound):
            store.complete(7)

    def test_complete_looks_up_by_id_not_position_after_removal(self):
        # Regression test for GH1: completing a surviving task by its id
        # must mark that task, not whatever happens to sit at the same
        # list position after an earlier task was removed.
        store = Store(self.path)
        store.add("a")
        store.add("b")
        store.add("c")
        store.remove(1)

        completed = store.complete(2)

        self.assertEqual(completed["id"], 2)
        by_id = {task["id"]: task for task in store.tasks}
        self.assertTrue(by_id[2]["done"])
        self.assertFalse(by_id[3]["done"])
