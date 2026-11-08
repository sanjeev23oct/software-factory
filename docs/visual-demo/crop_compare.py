#!/usr/bin/env python3
"""Two labelled panels from a visual_verify compare.png, cropped to the screen's content, for a video frame.

    python3 crop_compare.py COMPARE.png OUT.png --panels 0,1 --labels "Reference,Built"
    python3 crop_compare.py --screens REFERENCE.png,ACTUAL.png OUT.png --labels "Asked for,Built"

compare.png holds three 1280x800 panels (reference, built, difference) side by side; at video size each
is too small to read. This keeps two of them and only the part of the screen with content on it.
"""

import argparse
import base64
import subprocess
import tempfile
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PANEL_W, GAP, HEAD = 1280, 24, 44          # the layout visual_verify.mjs draws
CROP = (110, 0, 1060, 620)                  # x, y, width, height of each panel kept: the content area


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("compare", nargs="?")
    p.add_argument("--screens", help="two raw 1280x800 screenshots, comma-separated, instead of a compare.png")
    p.add_argument("out")
    p.add_argument("--panels", default="0,1")
    p.add_argument("--labels", default="Reference,Built")
    args = p.parse_args()
    x0, y0, w, h = CROP
    if args.screens:
        # Raw screens: each is a panel of its own, so offsets start at the screen's edge.
        sources = [Path(path) for path in args.screens.split(",")]
        panels = [(None, label) for label in args.labels.split(",")]
    else:
        sources = [Path(args.compare)] * 2
        panels = list(zip((int(n) for n in args.panels.split(",")), args.labels.split(",")))
    # Fill a video frame's picture area exactly (1208x596 at 2x), scaling the panels up to use it.
    width, height, pad, gap, caption = 2416, 1192, 40, 32, 58
    scale = min((width - 2 * pad - gap * (len(panels) - 1)) / (w * len(panels)), (height - 2 * pad - caption) / h)
    tiles = []
    for (panel, label), source in zip(panels, sources):
        src = "data:image/png;base64," + base64.b64encode(source.read_bytes()).decode()
        left, top, full = (x0, y0, PANEL_W) if panel is None else (GAP + panel * (PANEL_W + GAP) + x0, HEAD + y0, 3936)
        tiles.append('<figure><figcaption>{}</figcaption><div class="crop" style="width:{:.0f}px;height:{:.0f}px">'
                     '<img src="{}" style="left:-{:.0f}px;top:-{:.0f}px;width:{:.0f}px"></div></figure>'.format(
                         label, w * scale, h * scale, src, left * scale, top * scale, full * scale))
    page = ('<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;width:{}px;height:{}px;background:#0b121c}}'
            'body{{display:flex;gap:{}px;align-items:center;justify-content:center;font:700 40px Barlow,Arial,sans-serif;color:#e8eef7}}'
            'figure{{margin:0}}figcaption{{margin:0 0 14px}}'
            '.crop{{position:relative;overflow:hidden;border-radius:14px;border:3px solid #26344a}}.crop img{{position:absolute}}</style>{}').format(
                width, height, gap, "".join(tiles))
    with tempfile.TemporaryDirectory() as tmp:
        html = Path(tmp) / "page.html"
        html.write_text(page)
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size={},{}".format(width, height),
                        "--screenshot={}".format(Path(args.out).resolve()), html.as_uri()], capture_output=True, check=True)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
