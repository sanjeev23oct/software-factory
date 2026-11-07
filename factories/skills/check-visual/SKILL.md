---
name: check-visual
description: Checker: verify a built screen against its reference screenshot, measured by the visual verifier and then judged by eye, and write the evidence. Used by check-tasks when a gate asks for a visual check.
---
# check-visual (the visual checker)

You are the checker, in a separate session from the maker. You judge the screen in the checkout against its reference. You do not change code, and you do not change the contract or its thresholds: a person approved them.

The gate names a screen: `<spec folder>/reference/<screen>.json` and its image `<spec folder>/reference/<screen>.png`.

## 1. Measure

Run the verifier from the checkout root. The factory's scripts folder is named in your prompt.

```
node <factory scripts>/visual_verify.mjs --root . --contract <spec folder>/reference/<screen>.json --out <spec folder>/evidence/visual/<screen>
```

It prints PASS or FAIL per region and writes `actual.png`, `diff.png`, `compare.png` and `report.json` into the evidence folder. Exit 1 is a failed screen; exit 2 means it could not check: report that as a finding.

## 2. Judge

Open `compare.png` (reference, built, difference, each region boxed), then the reference and `actual.png` themselves. Go through this checklist, comparing the built screen with the reference:

1. **Layout and hierarchy:** the same areas, in the same order and arrangement (rows stay rows, columns stay columns).
2. **Spacing:** the gaps between areas and inside them are close to the reference's.
3. **Alignment:** edges that line up in the reference line up in the build.
4. **Type:** headings, labels and values have the same relative sizes and weights.
5. **Colour:** accents, status colours and backgrounds match where the reference uses them.
6. **States:** every state the visual spec lists that this section builds can be shown.
7. **Copy:** the exact words of the reference and the visual spec.

Write `<spec folder>/evidence/visual/<screen>/findings.json`:

```json
{"verdict": "FAIL",
 "findings": [{"region": "totals", "severity": "blocking",
               "issue": "the cards stack vertically; the reference shows them in one row",
               "evidence": "actual box 960x312 vs 960x104 in the reference; compare.png shows three stacked cards"}]}
```

Every finding names a region (or `page`), says what differs, and cites evidence you saw: a number from `report.json`, or what `compare.png` shows. `blocking` is a difference a person would notice and reject; `minor` is everything else. Do not report differences in masked areas or in sample data.

## 3. Decide

The screen passes only when the verifier passed **and** you have no blocking finding. Add a row for each to the section's evidence file:

```
| visual_verify.mjs <screen> | PASS | PASS (4 regions) | PASS |
| visual judgement (check-visual) | no blocking findings | 1 minor: footer 8px lower | PASS |
```

If it fails, copy each blocking finding and each failed region from the verifier into `factory_feedback.md`, with the region, what differs, and what the maker should change, and tick nothing.
