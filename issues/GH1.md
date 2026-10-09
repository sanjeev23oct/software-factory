---
title: `done` marks the wrong task after I delete one
author: priya
state: open
labels: needs-triage
---
I had three tasks. I removed the first one, then ran `done 3` and it said
"error: no task with id 3" even though `list` clearly shows task 3.

Then I ran `done 2` and it printed "done 3" and ticked off task 3 instead of 2!

Steps:

    python3 -m tasklite add "a"
    python3 -m tasklite add "b"
    python3 -m tasklite add "c"
    python3 -m tasklite rm 1
    python3 -m tasklite done 2
    python3 -m tasklite list

Expected task 2 to be checked. Task 3 is checked instead.
