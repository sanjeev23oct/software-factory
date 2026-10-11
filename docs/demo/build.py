#!/usr/bin/env python3
"""Build the demo video and the walkthrough page from the captures of a real run.

    python3 docs/demo/build.py

Everything shown comes from docs/demo/captures/ (real terminal output and the
documents agents wrote) and docs/demo/shots/ (real screenshots, taken by
drive.mjs together with the position of each thing worth pointing at). This
script only lays them out: one 1280x720 frame per scene, joined into
factory-demo.mp4, and the same scenes with more words as index.html.

The scenes are listed in story.json. Kinds of scene:
  title     the opening frame
  chapter   a section heading; may carry `points` (a list of terms) or `define`
  step      a numbered step on a page of its own, shown before its pictures
  image     a screenshot; its marks are numbered 1, 2, 3 and listed underneath
  doc       a document an agent wrote, with chosen lines highlighted
  terminal  terminal output, with chosen lines highlighted

Needs Google Chrome (to draw the frames) and ffmpeg (to join them).
"""

import html
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAPTURES, SHOTS, FRAMES = HERE / "captures", HERE / "shots", HERE / "frames"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PIC_W, PIC_H = 1208, 596   # the picture area; drive.mjs takes screenshots at exactly this size

CSS = """
:root { --bg: #0b121c; --panel: #121c2a; --ink: #e8eef7; --muted: #92a0b3; --line: #26344a;
  --r1: #6aa0ff; --r2: #4fd09a; --r3: #ef7cc9; --r4: #ffa154; --hot: #ff6a1a; --paper: #ffffff; --paper-ink: #0f1b2d; }
* { box-sizing: border-box; }
html, body { margin: 0; width: 1280px; height: 720px; overflow: hidden; background: var(--bg); color: var(--ink);
  font: 20px/1.45 "Barlow", "Helvetica Neue", Arial, sans-serif; }
.num { display: inline-grid; place-items: center; border-radius: 50%; background: var(--hot); color: #fff; font-weight: 700; flex: none;
  font-family: "Barlow", Arial, sans-serif; }

/* full pages: title, chapter, step */
.page { height: 720px; display: grid; align-content: center; gap: 22px; padding: 0 90px; }
.bars { display: flex; gap: 8px; } .bars i { width: 12px; height: 46px; border-radius: 6px; }
.kicker { font: 700 22px "Barlow Condensed", Arial, sans-serif; letter-spacing: .14em; text-transform: uppercase; color: var(--c, var(--r1)); }
.page h1 { margin: 0; font: 700 92px/0.96 "Barlow Condensed", "Arial Narrow", Arial, sans-serif; text-transform: uppercase; }
.page p { margin: 0; font-size: 30px; color: var(--muted); max-width: 27em; }
.page.title h1 { font-size: 150px; letter-spacing: -.01em; } .page.title h1 em { font-style: normal; color: var(--r4); }
.page .define { font-size: 34px; line-height: 1.3; color: var(--ink); max-width: 30em; } .define b { color: var(--r4); font-weight: 600; }
.page.wide { padding: 0 70px; gap: 16px; } .page.wide h1 { font-size: 64px; }
.points { display: grid; grid-template-columns: 1fr 1fr; gap: 12px 28px; margin-top: 8px; }
.points.one { grid-template-columns: 1fr; }
.points div { display: grid; grid-template-columns: 190px 1fr; gap: 14px; align-items: baseline; border-top: 1px solid var(--line); padding-top: 10px; }
.points b { font: 700 28px/1 "Barlow Condensed", Arial, sans-serif; text-transform: uppercase; color: var(--c2, var(--r1)); }
.points span { font-size: 21px; line-height: 1.3; }
.page.step { grid-template-columns: 200px 1fr; column-gap: 44px; align-items: center; align-content: center; }
.page.step .num { width: 190px; height: 190px; font-size: 104px; }
.page.step .of { font: 700 20px "Barlow Condensed", Arial, sans-serif; letter-spacing: .14em; text-transform: uppercase; color: var(--muted); }
.page.step h1 { font-size: 76px; margin: 6px 0 14px; }
.page.step p { font-size: 28px; }

/* picture pages: the picture on top, the caption and the numbered legend underneath */
.stage { height: 622px; padding: 26px 36px 0; }
.foot { height: 98px; padding: 0 36px; display: flex; align-items: center; gap: 16px; }
.foot .num { width: 46px; height: 46px; font-size: 24px; }
.foot .say { font-size: 23px; font-weight: 600; line-height: 1.2; flex: 0 1 auto; max-width: 560px; }
.foot .legend { margin-left: auto; display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 6px 18px; max-width: 640px; }
.foot .legend span { display: flex; align-items: center; gap: 8px; font-size: 18px; color: var(--ink); white-space: nowrap; }
.foot .legend .num { width: 28px; height: 28px; font-size: 16px; }
.badge { display: inline-flex; align-items: center; gap: 9px; font: 600 16px "Barlow", Arial, sans-serif; color: var(--r2); white-space: nowrap;
  border: 1.5px solid var(--r2); border-radius: 99px; padding: 5px 13px; }
.badge i { width: 10px; height: 10px; border-radius: 50%; background: var(--r2); }
.shot { height: 596px; border-radius: 12px; overflow: hidden; outline: 1px solid var(--line); background: #f2f4f7; position: relative; }
.shot img { width: 100%; display: block; }
.dim { position: absolute; left: 0; top: 0; }
.mark { position: absolute; border: 4px solid var(--hot); border-radius: 10px; box-shadow: 0 0 0 4px rgba(255, 106, 26, .25); }
.pin { position: absolute; width: 40px; height: 40px; font-size: 22px; border: 3px solid #fff; box-shadow: 0 3px 12px rgba(0, 0, 0, .45); }
.term { height: 596px; background: #070c13; border: 1px solid var(--line); border-radius: 12px; overflow: hidden; display: grid; grid-template-rows: 40px 1fr; }
.term .top { display: flex; align-items: center; gap: 7px; padding: 0 14px; border-bottom: 1px solid var(--line); color: var(--muted); font: 14px "IBM Plex Mono", Menlo, monospace; }
.term .top s { width: 11px; height: 11px; border-radius: 50%; background: var(--line); } .term .top span { margin-left: 10px; }
.term pre { margin: 0; padding: 18px 22px; font: 19px/1.6 "IBM Plex Mono", Menlo, monospace; white-space: pre-wrap; overflow: hidden; }
.term .cmd { color: var(--r1); } .term .hold { color: var(--r4); font-weight: 600; } .term .good { color: var(--r2); font-weight: 600; } .term .dim2 { color: var(--muted); }
.term .hl { background: #3a2a0c; box-shadow: -8px 0 0 #3a2a0c, 8px 0 0 #3a2a0c; color: #ffd27a; font-weight: 600; }
.doc { height: 596px; background: var(--paper); color: var(--paper-ink); border-radius: 12px; padding: 26px 34px; overflow: hidden; font-size: 17px; line-height: 1.5; position: relative; }
.doc::after { content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 70px; background: linear-gradient(transparent, var(--paper)); }
.doc h1 { font: 700 30px "Barlow Condensed", Arial, sans-serif; text-transform: uppercase; margin: 0 0 8px; }
.doc h2 { font: 700 22px "Barlow Condensed", Arial, sans-serif; text-transform: uppercase; margin: 14px 0 4px; color: #1f5fd0; }
.doc h3 { font-size: 17px; margin: 10px 0 2px; }
.doc p, .doc li { margin: 2px 0; } .doc ul { margin: 2px 0; padding-left: 22px; }
.doc code { font: 14.5px "IBM Plex Mono", Menlo, monospace; background: #e9edf3; padding: 1px 5px; border-radius: 4px; }
.doc pre { font: 14px/1.5 "IBM Plex Mono", Menlo, monospace; background: #0f1b2d; color: #e6ecf5; padding: 10px 14px; border-radius: 8px; margin: 6px 0; white-space: pre-wrap; }
.doc table { border-collapse: collapse; font-size: 15px; margin: 6px 0; } .doc td, .doc th { border: 1px solid #d6dce5; padding: 4px 10px; text-align: left; }
.doc .hl { background: #ffe9a8; box-shadow: -6px 0 0 #ffe9a8, 6px 0 0 #ffe9a8; border-radius: 2px; }
"""
FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700'
         '&family=Barlow+Condensed:wght@600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">')
BARS = ('<div class="bars"><i style="background:var(--r1)"></i><i style="background:var(--r2)"></i>'
        '<i style="background:var(--r3)"></i><i style="background:var(--r4)"></i></div>')


def inline(text):
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)


def markdown(text, highlight=()):
    """Enough markdown for specs and reports: headings, bullets, code blocks, tables, paragraphs."""
    out, in_code, in_list, in_table = [], False, False, False
    for line in text.splitlines():
        hot = ' class="hl"' if any(re.search(h, line) for h in highlight) else ""
        if line.strip().startswith("```"):
            out.append("</pre>" if in_code else "<pre>")
            in_code = not in_code
            continue
        if in_code:
            out.append(html.escape(line))
            continue
        bullet = re.match(r"^\s*(?:[-*]|\d+\.)\s+(.*)", line)
        if in_list and not bullet:
            out.append("</ul>")
            in_list = False
        row = line.strip().startswith("|")
        if in_table and not row:
            out.append("</table>")
            in_table = False
        heading = re.match(r"^(#{1,4})\s+(.*)", line)
        if heading:
            level = min(len(heading.group(1)), 3)
            out.append("<h{0}>{1}</h{0}>".format(level, inline(heading.group(2))))
        elif bullet:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append("<li><span{}>{}</span></li>".format(hot, inline(bullet.group(1))))
        elif row:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", c) for c in cells):
                continue
            if not in_table:
                out.append("<table>")
                in_table = True
            out.append("<tr{}>{}</tr>".format(hot, "".join("<td>{}</td>".format(inline(c)) for c in cells)))
        elif line.strip():
            out.append("<p><span{}>{}</span></p>".format(hot, inline(line)))
    return "\n".join(out + (["</ul>"] if in_list else []) + (["</table>"] if in_table else []) + (["</pre>"] if in_code else []))


def terminal(text, highlight=()):
    lines = []
    for line in text.splitlines():
        escaped = html.escape(line)
        if any(re.search(h, line) for h in highlight):
            escaped = '<span class="hl">{}</span>'.format(escaped)
        elif line.startswith("$ "):
            escaped = '<span class="cmd">{}</span>'.format(escaped)
        elif line.startswith(("# ", "==", "ITEM")):
            escaped = '<span class="dim2">{}</span>'.format(escaped)
        elif re.search(r"waiting|Waiting for", line):
            escaped = '<span class="hold">{}</span>'.format(escaped)
        elif re.search(r"approved|opened|Posted|OK\b|PASS|passed|Installed|done\b", line):
            escaped = '<span class="good">{}</span>'.format(escaped)
        lines.append(escaped)
    return "\n".join(lines)


def excerpt(name, start=None, end=None, lines=None, tail=None):
    text = (CAPTURES / name).read_text()
    if tail:
        return "\n".join(text.splitlines()[-tail:])
    if start:
        text = text[text.index(start):]
    if end and end in text:
        text = text[:text.index(end)]
    return "\n".join(text.splitlines()[:lines]) if lines else text


def marks_for(scene):
    """Numbered highlights for a picture. Returns (overlay html, [labels in number order]).
    Everything outside the highlighted boxes is dimmed once; each box gets a numbered pin on its corner."""
    path = SHOTS / (Path(scene["image"]).stem + ".json")
    if not path.exists() or scene.get("marks") is False:
        return "", []
    boxes, labels = [], []
    for mark in json.loads(path.read_text()):
        x, y, w, h = mark["box"]
        x, y, w, h = max(x - 6, 2), max(y - 6, 2), min(w + 12, PIC_W - 4), h + 12
        if y > PIC_H - 8 or y + h < 8:
            continue
        boxes.append((x, y, min(w, PIC_W - 2 - x), min(h, PIC_H - 4 - y)))
        labels.append(mark["label"])
    if not boxes:
        return "", []
    holes = "".join('<rect x="{}" y="{}" width="{}" height="{}" rx="10" fill="black"/>'.format(*box) for box in boxes)
    out = ['<svg class="dim" width="{0}" height="{1}"><defs><mask id="holes"><rect width="{0}" height="{1}" fill="white"/>{2}</mask></defs>'
           '<rect width="{0}" height="{1}" fill="rgba(8,14,24,.45)" mask="url(#holes)"/></svg>'.format(PIC_W, PIC_H, holes)]
    for n, (x, y, w, h) in enumerate(boxes, 1):
        out.append('<div class="mark" style="left:{}px;top:{}px;width:{}px;height:{}px"></div>'.format(x, y, w, h))
        out.append('<div class="num pin" style="left:{}px;top:{}px">{}</div>'.format(
            min(max(x - 20, 2), PIC_W - 44), min(max(y - 20, 2), PIC_H - 44), n))
    return "".join(out), labels


def body_of(scene):
    kind = scene["kind"]
    e = html.escape
    if kind == "title":
        return '<div class="page title">{}<div class="kicker">{}</div><h1>{}</h1><p>{}</p></div>'.format(
            BARS, e(scene["kicker"]), scene["title"], e(scene["say"]))
    if kind == "chapter" and scene.get("points"):
        rows = "".join('<div style="--c2:{}"><b>{}</b><span>{}</span></div>'.format(c, e(t), e(m)) for t, m, c in scene["points"])
        return '<div class="page wide"><div class="kicker">{}</div><h1>{}</h1><div class="points{}">{}</div></div>'.format(
            e(scene["kicker"]), e(scene["title"]), " one" if scene.get("one_column") else "", rows)
    if kind == "chapter":
        text = '<p class="define">{}</p>'.format(scene["define"]) if scene.get("define") else "<p>{}</p>".format(e(scene.get("say", "")))
        return '<div class="page" style="--c:{}">{}<div class="kicker">{}</div><h1>{}</h1>{}</div>'.format(
            scene.get("colour", "var(--r1)"), BARS, e(scene["kicker"]), e(scene["title"]), text)
    if kind == "step":
        return ('<div class="page step"><div class="num">{}</div><div><div class="of">Step {} of {}</div><h1>{}</h1><p>{}</p></div></div>').format(
            scene["n"], scene["n"], scene["of"], e(scene["title"]), e(scene["say"]))

    legend = []
    if kind == "terminal":
        inner = '<div class="term"><div class="top"><s></s><s></s><s></s><span>{}</span></div><pre>{}</pre></div>'.format(
            e(scene.get("where", "terminal")), terminal(scene["text"], scene.get("highlight", ())))
    elif kind == "doc":
        inner = '<div class="doc">{}</div>'.format(markdown(scene["text"], scene.get("highlight", ())))
    else:
        overlay, legend = marks_for(scene)
        inner = '<div class="shot"><img src="../shots/{}" style="margin-top:-{}px">{}</div>'.format(scene["image"], scene.get("offset", 0), overlay)
    number = '<span class="num">{}</span>'.format(scene["n"]) if scene.get("n") else ""
    keys = "".join('<span><i class="num">{}</i>{}</span>'.format(i, e(label)) for i, label in enumerate(legend, 1))
    badge = '<span class="badge"><i></i>running in the background</span>' if scene.get("background") else ""
    right = '<div class="legend">{}{}</div>'.format(keys, badge) if (keys or badge) else ""
    return '<div class="stage">{}</div><div class="foot">{}<span class="say">{}</span>{}</div>'.format(inner, number, e(scene["say"]), right)


def draw(scenes):
    FRAMES.mkdir(exist_ok=True)
    for old in FRAMES.glob("*"):
        old.unlink()
    for i, scene in enumerate(scenes):
        page = FRAMES / "{:02d}.html".format(i + 1)
        page.write_text('<!doctype html><html><head><meta charset="utf-8">{}<style>{}</style></head><body>{}</body></html>'.format(
            FONTS, CSS, body_of(scene)))
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1280,720",
                        "--virtual-time-budget=4000", "--screenshot={}".format(page.with_suffix(".png")), page.as_uri()],
                       capture_output=True)
        scene["frame"] = page.with_suffix(".png").name
        page.unlink()
        if not (FRAMES / scene["frame"]).exists():
            sys.exit("could not draw frame {}".format(i + 1))


def video(scenes):
    listing = FRAMES / "frames.txt"
    lines = []
    for scene in scenes:
        lines += ["file '{}'".format(scene["frame"]), "duration {}".format(scene.get("seconds", 6))]
    lines.append("file '{}'".format(scenes[-1]["frame"]))  # the concat demuxer needs the last frame named twice
    listing.write_text("\n".join(lines) + "\n")
    out = HERE / "factory-demo.mp4"
    proc = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                           "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "20", "-movflags", "+faststart", str(out)],
                          capture_output=True, text=True)
    listing.unlink()
    if proc.returncode:
        sys.exit("ffmpeg failed: " + proc.stderr[-400:])
    return out


PAGE_CSS = """
:root { --bg: #f2f4f7; --paper: #fff; --ink: #0f1b2d; --muted: #5d6b7e; --line: #d6dce5; --accent: #1f5fd0; --hot: #e2580f; --code: #0f1b2d; --code-ink: #e6ecf5; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg: #0b121c; --paper: #121c2a; --ink: #e8eef7; --muted: #92a0b3; --line: #26344a; --accent: #6aa0ff; --hot: #ff7a2e; --code: #070c13; color-scheme: dark; } }
:root[data-theme="dark"] { --bg: #0b121c; --paper: #121c2a; --ink: #e8eef7; --muted: #92a0b3; --line: #26344a; --accent: #6aa0ff; --hot: #ff7a2e; --code: #070c13; color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 17px/1.55 "Barlow", "Helvetica Neue", Arial, sans-serif; }
.wrap { max-width: 980px; margin: 0 auto; padding-inline: 20px; padding-block: 40px 80px; display: grid; gap: 52px; }
h1 { margin: 0; font: 700 clamp(48px, 9vw, 104px)/0.92 "Barlow Condensed", "Arial Narrow", Arial, sans-serif; text-transform: uppercase; text-wrap: balance; }
h2 { margin: 0; font: 700 38px/1 "Barlow Condensed", Arial, sans-serif; text-transform: uppercase; text-wrap: balance; }
h3 { margin: 0; font: 600 22px/1.25 "Barlow", Arial, sans-serif; display: flex; gap: 12px; align-items: center; }
h3 i { font-style: normal; display: inline-grid; place-items: center; width: 38px; height: 38px; border-radius: 50%; background: var(--hot); color: #fff; font-weight: 700; flex: none; }
p { margin: 0; max-width: 66ch; } a { color: var(--accent); }
header { display: grid; gap: 16px; } header p { font-size: 20px; color: var(--muted); }
video, figure img { width: 100%; display: block; border-radius: 12px; border: 1px solid var(--line); background: #0b121c; }
section { display: grid; gap: 16px; min-width: 0; }
.step { display: grid; gap: 12px; padding-top: 18px; border-top: 1px solid var(--line); min-width: 0; }
.part { font: 700 14px "Barlow Condensed", Arial, sans-serif; letter-spacing: .12em; text-transform: uppercase; color: var(--accent); }
figure { margin: 0; display: grid; gap: 8px; } figcaption { font-size: 14px; color: var(--muted); }
.how { background: var(--paper); border: 1px solid var(--line); border-radius: 12px; padding: 16px 18px; display: grid; gap: 8px; min-width: 0; }
.how b { font: 700 16px "Barlow Condensed", Arial, sans-serif; letter-spacing: .08em; text-transform: uppercase; }
pre { margin: 0; background: var(--code); color: var(--code-ink); border-radius: 8px; padding: 12px 14px; font: 13.5px/1.6 "IBM Plex Mono", Menlo, monospace; white-space: pre-wrap; overflow-wrap: anywhere; }
code { font: 0.9em "IBM Plex Mono", Menlo, monospace; }
.terms { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr)); gap: 10px; }
.terms div { background: var(--paper); border: 1px solid var(--line); border-radius: 12px; padding: 12px 16px; }
.terms b { display: block; font: 700 22px/1.1 "Barlow Condensed", Arial, sans-serif; text-transform: uppercase; color: var(--accent); } .terms span { font-size: 15px; }
.facts { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 200px), 1fr)); gap: 12px; }
.facts div { background: var(--paper); border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px; }
.facts b { display: block; font: 700 30px/1 "Barlow Condensed", Arial, sans-serif; } .facts span { font-size: 14px; color: var(--muted); }
ul { margin: 0; padding-left: 20px; display: grid; gap: 4px; max-width: 66ch; }
footer { color: var(--muted); font-size: 14px; }
"""


def page(story):
    e, out, open_step = html.escape, [], False
    figure = lambda s: '<figure><img src="frames/{}" alt="{}" loading="lazy"></figure>'.format(s["frame"], e(s["say"]))
    for scene in story["scenes"]:
        kind = scene["kind"]
        if kind in ("title",):
            continue
        if kind in ("chapter", "step") and open_step:
            out.append("</div>")
            open_step = False
        if kind == "chapter":
            if out:
                out.append("</section>")
            out.append('<section><span class="part">{}</span><h2>{}</h2><p>{}</p>'.format(
                e(scene["kicker"]), e(scene["title"]), scene.get("explain", scene.get("define", e(scene.get("say", ""))))))
            if scene.get("points"):
                out.append('<div class="terms">{}</div>'.format("".join("<div><b>{}</b><span>{}</span></div>".format(e(t), e(m)) for t, m, _ in scene["points"])))
            if scene.get("how"):
                out.append('<div class="how"><b>Do this yourself</b>{}</div>'.format(scene["how"]))
        elif kind == "step":
            out.append('<div class="step"><h3><i>{}</i>{}</h3><p>{}</p>'.format(scene["n"], e(scene["title"]), scene.get("explain", e(scene["say"]))))
            if scene.get("how"):
                out.append('<div class="how"><b>Do this yourself</b>{}</div>'.format(scene["how"]))
            open_step = True
        else:
            out.append(figure(scene))
    out.append("</div>" if open_step else "")
    out.append("</section>")
    facts = "".join("<div><b>{}</b><span>{}</span></div>".format(e(str(v)), e(k)) for k, v in story["facts"])
    links = "".join('<li><a href="{}">{}</a></li>'.format(e(u), e(t)) for t, u in story["links"])
    first = story["scenes"][0]
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            "<title>Idea to Value</title>{}<style>{}</style></head><body><div class=\"wrap\">"
            "<header><span class=\"part\">{}</span><h1>Idea to Value</h1><p>{}</p>"
            '<video src="factory-demo.mp4" controls preload="metadata" poster="frames/{}"></video></header>'
            '<div class="facts">{}</div>{}'
            "<section><h2>See it for yourself</h2><ul>{}</ul></section>"
            "<footer>Frames and video are built by docs/demo/build.py from the captured output of a real run. Nothing is mocked.</footer>"
            "</div></body></html>\n").format(FONTS, PAGE_CSS, e(first["kicker"]), e(story["intro"]), first["frame"], facts, "".join(out), links)


def main():
    story = json.loads((HERE / "story.json").read_text())
    scenes = story["scenes"]
    for scene in scenes:
        if "file" in scene:
            scene["text"] = excerpt(scene["file"], scene.get("start"), scene.get("end"), scene.get("lines"), scene.get("tail"))
    draw(scenes)
    out = video(scenes)
    (HERE / "index.html").write_text(page(story))
    seconds = sum(s.get("seconds", 6) for s in scenes)
    print("{} scenes, {}:{:02d}  {}  {:.1f} MB".format(len(scenes), seconds // 60, seconds % 60, out.name, out.stat().st_size / 1e6))


if __name__ == "__main__":
    main()
