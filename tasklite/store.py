"""JSON-file-backed task storage."""

import json
import os


class TaskNotFound(Exception):
    pass


class Store:
    def __init__(self, path):
        self.path = path
        self.next_id = 1
        self.tasks = []
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            self.next_id = data["next_id"]
            self.tasks = data["tasks"]

    def save(self):
        with open(self.path, "w") as f:
            json.dump({"next_id": self.next_id, "tasks": self.tasks}, f, indent=2)

    def add(self, title):
        task = {"id": self.next_id, "title": title, "done": False}
        self.next_id += 1
        self.tasks.append(task)
        return task

    def _find_index(self, task_id):
        for i, task in enumerate(self.tasks):
            if task["id"] == task_id:
                return i
        raise TaskNotFound(task_id)

    def complete(self, task_id):
        task = self.tasks[self._find_index(task_id)]
        task["done"] = True
        return task

    def remove(self, task_id):
        return self.tasks.pop(self._find_index(task_id))
