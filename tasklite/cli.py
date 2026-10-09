"""Command-line interface: python3 -m tasklite [--db PATH] <command>."""

import argparse
import sys

from tasklite.store import Store, TaskNotFound


def build_parser():
    parser = argparse.ArgumentParser(prog="tasklite")
    parser.add_argument("--db", default="tasks.json", help="path to the task file")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add a task")
    add.add_argument("title")

    sub.add_parser("list", help="list tasks")

    done = sub.add_parser("done", help="mark a task as done")
    done.add_argument("id", type=int)

    rm = sub.add_parser("rm", help="remove a task")
    rm.add_argument("id", type=int)

    return parser


def format_task(task):
    mark = "x" if task["done"] else " "
    return "[{}] {:>3}  {}".format(mark, task["id"], task["title"])


def main(argv=None, out=sys.stdout, err=sys.stderr):
    args = build_parser().parse_args(argv)
    store = Store(args.db)

    try:
        if args.command == "add":
            task = store.add(args.title)
            store.save()
            print("added {}".format(task["id"]), file=out)
        elif args.command == "list":
            for task in store.tasks:
                print(format_task(task), file=out)
        elif args.command == "done":
            task = store.complete(args.id)
            store.save()
            print("done {}".format(task["id"]), file=out)
        elif args.command == "rm":
            task = store.remove(args.id)
            store.save()
            print("removed {}".format(task["id"]), file=out)
    except TaskNotFound as e:
        print("error: no task with id {}".format(e), file=err)
        return 1
    return 0
