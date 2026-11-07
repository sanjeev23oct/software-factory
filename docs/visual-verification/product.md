# Visual verification: product spec

## The problem

The factory can prove that a change has the right text, the right test ids,
and passing tests. It cannot prove that a screen looks like the design it was
asked to match. The `ui-app` pipeline says so in its README, and ends with a
person looking at the result.

That is the weakest link in the factory. Verification is what lets agents run
without someone reading every line; where verification stops, autonomy stops.
For UI work today, a person is the verifier.

## What we want

When a request comes with a reference screenshot, the factory checks the
screens it built against that reference, in three layers, and leaves evidence
a person can read in seconds:

1. **Measured.** A script renders the built screen and compares it with the
   reference: where each element is, what it says, what colour it is, and how
   similar each region looks. The same build always gives the same numbers.
2. **Judged.** A separate checker agent, which never saw the maker work and
   cannot change code, compares the two images against a fixed checklist and
   reports blocking findings with evidence.
3. **Accepted.** The person at the gate sees the reference, the result and a
   difference heatmap side by side, with the findings, before they approve.

And we want to **prove the verifier works**: show that it fails every planted
visual defect and passes harmless variation, with numbers, on every change to
the verifier itself.

## Who it's for

- **The person asking**, who attaches a screenshot or mockup and wants the
  result to match it.
- **The person approving**, who should be able to judge a screen from one
  image, not by clicking through the app.
- **The factory engineer**, who needs to trust the verifier enough to let UI
  sections run without review, and to see when it gets things wrong.

## Stories

### 1. The reference becomes a contract

As the person asking, I attach a reference screenshot to my issue, so that the
factory builds to it.

- AC 1.1: A PNG attached to the issue is saved with the request's spec as
  `reference/<screen>.png`.
- AC 1.2: The visual-spec stage writes `reference/<screen>.json`: the viewport,
  and named regions on the reference, each with its box, the `data-testid`
  that must fill it, any exact text, and any colours.
- AC 1.3: The region file is approved with the requirements, at the first gate.
- AC 1.4: A request with no reference screenshot skips visual verification and
  says so in its progress comment.

### 2. Measured checks

As the factory engineer, I want measurable differences caught by a script, so
that the checker agent only spends its judgement on what can't be measured.

- AC 2.1: The screen is rendered in headless Chrome at the reference viewport,
  with fixed sample data, fonts loaded and animations off.
- AC 2.2: For each region: the element exists and is visible; its box overlaps
  the reference box by at least the region's threshold (default IoU 0.8); its
  text matches exactly; its colours are within the threshold (default ΔE 5).
- AC 2.3: Each region gets a perceptual similarity score against the
  reference, with listed dynamic areas masked out, and a threshold.
- AC 2.4: The script writes `actual.png`, `diff.png`, `compare.png`
  (reference, actual, diff side by side) and `visual-report.json` with every
  value and threshold, and exits non-zero if any region fails.
- AC 2.5: Two runs on the same build give identical reports.

### 3. Judged checks

As the factory engineer, I want a separate agent to judge what can't be
measured, so that "it looks off" is caught before a person sees it.

- AC 3.1: For UI sections, the checker receives the reference, the actual
  screenshot, the diff and the region report, and a fixed checklist: layout and
  hierarchy, spacing, alignment, type scale, colour, states, copy.
- AC 3.2: It writes findings as JSON: region, issue, severity (blocking or
  minor), and the evidence for each.
- AC 3.3: Only blocking findings fail the section. A failed section goes back
  to a new maker with the findings, up to the pipeline's attempt limit.
- AC 3.4: The checker cannot change code or its own thresholds.

### 4. Accepted by a person, then kept

As the person approving, I want to see the reference and the result side by
side, so that I can approve or reject in seconds.

- AC 4.1: The "waiting for you" comment at the screens gate shows
  `compare.png` and the findings, and links the full report.
- AC 4.2: Approving makes the actual screenshot the screen's baseline.
- AC 4.3: Later requests check screens they didn't mean to change against
  their baselines, strictly, so a change elsewhere can't quietly break them.

### 5. Proof that the verifier works

As the factory engineer, I want the verifier tested like any other code, so
that I can let it gate work.

- AC 5.1: A suite takes a known-good screen and plants one defect at a time:
  an element moved 24px, a colour swapped, a font shrunk, a component removed,
  a label changed, a row wrapped. Each must fail.
- AC 5.2: The suite also applies harmless variations: different sample data
  in masked areas, a sub-pixel shift, a near-identical page background. Each
  must pass.
- AC 5.3: It reports the catch rate and the false-alarm rate, and runs in
  presubmit, so a change that weakens the verifier fails.
- AC 5.4: Every time a person approves a screen the verifier failed, or
  rejects one it passed, the factory records it as a verifier miss, for the
  meta loop to learn from.

## Out of scope

- Matching a design tool's file directly (Figma and so on). The reference is
  a screenshot.
- Pixel-perfect matching of a mockup. Mockups and real browsers differ; the
  thresholds say how close is close enough.
- Animation and interaction checks beyond the states the visual spec lists.
- Automatic tuning of thresholds. The meta loop records misses; a person
  changes thresholds and checklists.
