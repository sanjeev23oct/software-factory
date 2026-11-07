# Visual verification: tech spec

How the factory checks built screens against a reference screenshot. The
behaviour is in [product.md](product.md).

## Where it sits

The `ui-app` pipeline gains one script stage and changes two existing ones.
Nothing changes for a request without a reference screenshot.

```
read-issue        saves attached PNGs to {spec}/reference/              (changed)
requirements → approve-requirements
visual-spec       also writes {spec}/reference/<screen>.json            (changed)
tasks → lint-tasks
build             UI sections: maker → visual checker → findings → maker (inner loop)
check-evidence → verify
visual-verify     new script stage: measured checks + baselines          (outer loop)
preview
approve-screens   comment shows compare.png and the findings
merge-request
```

## Files

```
{spec}/reference/dashboard.png          the reference, from the issue
{spec}/reference/dashboard.json         the contract, written by visual-spec
{spec}/evidence/visual/dashboard/
    actual.png  diff.png  compare.png   rendered and compared by visual-verify
    report.json                         every value and threshold
    findings.json                       the visual checker's judgement
baselines/<screen>.png                  on main, written when approve-screens passes
```

`reference/<screen>.json`:

```json
{
  "url": "index.html",
  "viewport": [1280, 800],
  "data": "data/sample.json",
  "mask": [[40, 640, 1200, 40]],
  "regions": [
    {"name": "totals", "testid": "totals", "box": [40, 96, 1200, 120],
     "text": ["Customers", "Open deal value", "Deals won"], "iou": 0.8, "similarity": 0.85},
    {"name": "table", "testid": "customers", "box": [40, 240, 1200, 380]}
  ],
  "colors": {"accent": "#1f5fd0", "ink": "#172033"}
}
```

Boxes are `[x, y, width, height]` in reference pixels. Per-region thresholds
override the defaults (IoU 0.8, similarity 0.85, ΔE 5).

## visual-verify (the measured layer)

`factory/scripts/visual_verify.mjs`, run with Node's built-ins and headless
Chrome, the same way `docs/demo/drive.mjs` drives Chrome. No third-party
packages: Chrome renders the screen **and** does the image arithmetic, on a
canvas, in the same session.

1. **Render.** Serve the checkout as static files. Open `url` at `viewport`,
   device scale 1, with `prefers-reduced-motion`, a fixed clock, and
   `document.fonts.ready` awaited. Capture `actual.png`.
2. **Measure each region.** Find `[data-testid=…]`; record visibility, its box,
   its text and its computed colours. Score:
   - geometry: IoU of the element's box with the reference box;
   - text: every listed string present, exactly;
   - colour: CIEDE2000 ΔE between computed and reference colours;
   - similarity: SSIM of the region in both images, greyscale, 8×8 windows,
     masked areas excluded.
3. **Draw the evidence.** `diff.png` is a heatmap of per-pixel difference;
   `compare.png` puts reference, actual and diff side by side with each
   region's box and result drawn on.
4. **Report and decide.** `report.json` holds every value, threshold and
   verdict. Exit 0 only if every region passes. Rendering is deterministic, so
   the same build gives a byte-identical report (AC 2.5); the suite checks this.

`check_evidence.py` already re-runs a checker's commands rather than trusting
its evidence. It treats `report.json` the same way: it re-runs
`visual_verify.mjs` and compares.

## The visual checker (the judged layer)

A new skill, `check-visual`, for the checker session on sections that touch a
screen with a reference. It receives the reference, `actual.png`, `diff.png`,
`report.json` and this checklist, and must return `findings.json`:

```json
{"verdict": "FAIL",
 "findings": [{"region": "totals", "severity": "blocking",
               "issue": "cards stack vertically; the reference shows one row",
               "evidence": "actual box 360px tall vs 120px in the reference; similarity 0.41"}]}
```

Checklist: layout and hierarchy, spacing rhythm, alignment, type scale,
colour, every listed state, copy. Rules: a finding must cite a region and
evidence; only `blocking` fails; no code changes (the harness already rejects
a checker that changes code); the thresholds in `reference/*.json` are not the
checker's to change, since they're written by visual-spec and approved by a
person.

## Gate and baselines

`approve-screens` embeds `compare.png` in its "waiting for you" comment, with
the findings and a link to `report.json`. When it passes, `actual.png` is
copied to `baselines/<screen>.png` on the work branch, so it merges with the
change. On later requests, `visual-verify` also renders every screen that has
a baseline and that the request didn't name, and compares strictly
(similarity ≥ 0.98 by default). An unintended change fails with its own
`compare.png`.

## Proving the verifier (AC 5)

`tests/visual/` holds a known-good screen, its reference, and a mutation suite
run by `./script/presubmit`:

| Planted defect | Expected |
|---|---|
| Element moved 24px | FAIL (geometry) |
| Accent colour swapped | FAIL (colour) |
| Heading font 20% smaller | FAIL (similarity) |
| A component removed | FAIL (missing element) |
| A label changed | FAIL (text) |
| A row wraps to two lines | FAIL (geometry, similarity) |
| Different data in a masked area | PASS |
| Sub-pixel anti-aliasing difference | PASS |
| A scrollbar appears | PASS |
| The same build verified twice | identical reports |

The suite prints the catch rate and the false-alarm rate, and fails if either
gets worse than its recorded value. A change to thresholds, the checklist or
the script has to keep the verifier at least as strong as it was.

## The meta loop

When a person approves a screen `visual-verify` or the checker failed, or
rejects one they passed, `flow.py` logs a `verifier miss` event with the
screen, the report and the person's comment. `flow.py page` and the progress
comment show the count. Misses are the input for changing thresholds,
checklists and the `check-visual` skill. Today a person makes those changes,
as with the other loops.

## What it needs on the runner

- Chrome or Chromium on the runner image, for `visual_verify.mjs`.
- Node, which the runner already has for `node --test`.
- The checker session needs to read images. Claude Code reads PNGs with its
  file-reading tool, so no new permission is needed.

## Rollout

1. `visual_verify.mjs` and the mutation suite, proven on the demo CRM screen.
2. `read-issue` and `visual-spec` changes: references and region files.
3. The `check-visual` skill in the build stage's checker.
4. The gate comment and baselines.
5. The `verifier miss` events.

Each step is useful on its own and lands with its tests.

## Risks

- **Mockups aren't browsers.** A design tool's rendering differs from Chrome's.
  Per-region thresholds and masks absorb this; the mutation suite shows they
  aren't so loose that real defects pass.
- **Thresholds drift towards "pass".** Only a person changes them, and the
  suite fails if the verifier gets weaker.
- **Fonts and data make renders flaky.** Fixed data, awaited fonts, reduced
  motion and a fixed clock make rendering deterministic; AC 2.5 checks it.
- **The checker agent rubber-stamps.** It must cite evidence for every
  finding, and the measured layer runs regardless of what it says.
