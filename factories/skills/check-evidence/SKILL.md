---
name: check-evidence
description: Verify ticked tasks are backed by PASS evidence and re-run Cat 1 checks. A script; no judgment involved.
---
# check-evidence

    python3 <factory>/factory/scripts/check_evidence.py --spec <spec folder> --repo . --cat1

It fails when a section has ticked tasks but no PASS evidence file, when a box is ticked with a "deferred" or "not written" note, or when a Cat 1 check does not return its EXPECTED value. On failure the factory sends the findings back to `build-tasks`.
