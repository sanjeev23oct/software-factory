---
name: write-visual-spec
description: Write visual-spec.md for UI work: every screen and state described precisely enough to build and to check; and, for each reference screenshot, the contract the visual check measures against.
---
# write-visual-spec

Write `<spec folder>/visual-spec.md`, and one `<spec folder>/reference/<screen>.json` for each reference screenshot in `<spec folder>/reference/`. Change nothing else.

Work from the mockups or screenshots attached to the requirement when there are any, and from the app's existing screens and component library otherwise. Say which you used. Open every image in `reference/` and look at it before you write.

## visual-spec.md

For each screen:

- layout, top to bottom, naming the existing components to reuse
- exact visible text: headings, button labels, empty-state and error messages
- every state: loading, empty, populated, error, disabled
- a `data-testid` for each interactive element and for each region below, so tests, checker greps and the visual check can find it
- keyboard and focus behavior where it matters

Where no mockup settles a choice, pick the option closest to an existing screen and list it under **Needs clarification**.

## reference/<screen>.json: the contract the visual check measures

For each image `reference/<screen>.png` (or `.jpg`), write `reference/<screen>.json` next to it. This is what "looks like the reference" means; a person approves it with the requirements.

1. **Viewport.** Read the image's size: `python3 -c "import struct,sys; f=open(sys.argv[1],'rb'); f.read(16); print(*struct.unpack('>II', f.read(8)))" reference/<screen>.png`. That is the viewport in CSS pixels, unless the image is wider than 1600 pixels: then it was taken on a high-density screen, and the viewport is half of each.
2. **Regions.** Name the 3 to 8 areas the request is about: a heading, a row of summary cards, a table, a form, a toolbar. Not every element; the ones whose place, words or colour matter. For each:
   - `name`: short, lowercase, with dashes
   - `testid`: the `data-testid` the visual spec gives that area (or `selector`, a CSS selector, for an element that has an id or is unique)
   - `box`: `[x, y, width, height]` in viewport pixels, measured on the reference image, to the nearest 8 pixels
   - `text`: the exact words that must appear in it, when they matter
   - `color` and `background`: `#rrggbb`, only where the colour is part of the design (an accent, a status colour)
3. **Thresholds.** You estimated the boxes from an image, so set `"iou": 0.6` on each region. Set `"similarity": false` on each region: a design and a browser render pixels differently, so similarity is for baselines, which the factory writes itself.
4. **Mask.** List in `mask` the boxes whose content is sample data that will differ, such as table rows.

```json
{
  "name": "customers",
  "reference": "customers.png",
  "url": "index.html",
  "viewport": [1280, 800],
  "mask": [[160, 250, 960, 270]],
  "regions": [
    {"name": "heading", "selector": "h1", "box": [160, 40, 960, 40], "text": ["Customers"], "iou": 0.6, "similarity": false},
    {"name": "totals", "testid": "totals", "box": [160, 96, 960, 104], "text": ["Customers", "Open deal value"], "iou": 0.6, "similarity": false},
    {"name": "open-value", "testid": "total-open-value", "box": [504, 136, 272, 40], "color": "#1f5fd0", "iou": 0.6, "similarity": false}
  ]
}
```

Every `testid` in a contract must appear in visual-spec.md, so the builder knows to use it.
