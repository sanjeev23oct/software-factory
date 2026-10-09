---
title: Traceback when the task file is empty
author: dana
state: open
labels: needs-triage
---
My disk filled up and tasks.json ended up as a 0 byte file. Now every command dumps a Python traceback:

    $ python3 -m tasklite list
    Traceback (most recent call last):
      ...
    json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

I get that the file is broken, but I would expect a normal error message telling me which file is bad, not a stack trace.
