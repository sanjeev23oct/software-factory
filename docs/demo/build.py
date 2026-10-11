#!/usr/bin/env python3
"""Build the demo video and the walkthrough page from the captures of a real run.

    python3 docs/demo/build.py

Everything shown comes from docs/demo/captures/ (real terminal output and the
documents agents wrote) and docs/demo/shots/ (real screenshots). This script
only lays them out: one 1280x720 frame per scene, joined into factory-demo.mp4,
and the same scenes with more words as index.html.

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

CSS = """
:root { --bg: #0b121c; --panel: #121c2a; --ink: #e8eef7; --muted: #92a0b3; --line: #26344a;
  --r1: #6aa0ff; --r2: #4fd09a; --r3: #ef7cc9; --r4: #ffa154; --paper: #ffffff; --paper-ink: #0f1b2d; }
* { box-sizing: border-box; }
html, body { margin: 0; width: 1280px; height: 720px; overflow: hidden; background: var(--bg); color: var(--ink);
  font: 20px/1.45 "Barlow", "Helvetica Neue", Arial, sans-serif; }
.bar { height: 76px; padding: 0 36px; display: flex; align-items: center; gap: 18px; border-bottom: 1px solid var(--line); }
.bar .part { font: 700 17px "Barlow Condensed", Arial, sans-serif; letter-spacing: .1em; text-transform: uppercase; color: var(--c, var(--r1));
  border: 2px solid var(--c, var(--r1)); border-radius: 99px; padding: 4px 14px; white-space: nowrap; }
.bar .say { font-size: 22px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.stage { height: 644px; padding: 22px 36px 26px; }
.card { height: 720px; display: grid; align-content: center; gap: 22px; padding: 0 90px; }
.card .bars { display: flex; gap: 8px; } .card .bars i { width: 12px; height: 46px; border-radius: 6px; }
.card .kicker { font: 700 22px "Barlow Condensed", Arial, sans-serif; letter-spacing: .14em; text-transform: uppercase; color: var(--c, var(--r1)); }
.card h1 { margin: 0; font: 700 92px/0.96 "Barlow Condensed", "Arial Narrow", Arial, sans-serif; text-transform: uppercase; letter-spacing: -.005em; }
.card p { margin: 0; font-size: 30px; color: var(--muted); max-width: 26em; }
.term { height: 100%; background: #070c13; border: 1px solid var(--line); border-radius: 12px; overflow: hidden; display: grid; grid-template-rows: 40px 1fr; }
.term .top { display: flex; align-items: center; gap: 7px; padding: 0 14px; border-bottom: 1px solid var(--line); color: var(--muted); font: 14px "IBM Plex Mono", Menlo, monospace; }
.term .top s { width: 11px; height: 11px; border-radius: 50%; background: var(--line); } .term .top span { margin-left: 10px; }
.term pre { margin: 0; padding: 18px 20px; font: 17px/1.55 "IBM Plex Mono", Menlo, monospace; white-space: pre-wrap; overflow: hidden; }
.term .cmd { color: var(--r1); } .term .hold { color: var(--r4); font-weight: 600; } .term .good { color: var(--r2); font-weight: 600; } .term .dim { color: var(--muted); }
.doc { height: 100%; background: var(--paper); color: var(--paper-ink); border-radius: 12px; padding: 26px 34px; overflow: hidden; font-size: 17px; line-height: 1.5; position: relative; }
.doc::after { content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 70px; background: linear-gradient(transparent, var(--paper)); }
.doc h1 { font: 700 30px "Barlow Condensed", Arial, sans-serif; text-transform: uppercase; margin: 0 0 8px; }
.doc h2 { font: 700 22px "Barlow Condensed", Arial, sans-serif; text-transform: uppercase; margin: 14px 0 4px; color: #1f5fd0; }
.doc h3 { font-size: 17px; margin: 10px 0 2px; }
.doc p, .doc li { margin: 2px 0; } .doc ul { margin: 2px 0; padding-left: 22px; }
.doc code { font: 14.5px "IBM Plex Mono", Menlo, monospace; background: #e9edf3; padding: 1px 5px; border-radius: 4px; }
.doc pre { font: 14px/1.5 "IBM Plex Mono", Menlo, monospace; background: #0f1b2d; color: #e6ecf5; padding: 10px 14px; border-radius: 8px; margin: 6px 0; white-space: pre-wrap; }
.doc table { border-collapse: collapse; font-size: 15px; margin: 6px 0; } .doc td, .doc th { border: 1px solid #d6dce5; padding: 4px 10px; text-align: left; }
.shot { height: 100%; border-radius: 12px; overflow: hidden; border: 1px solid var(--line); background: #f2f4f7; }
.shot img { width: 100%; display: block; }
"""
FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;600'
         '&family=Barlow+Condensed:wght@600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">')
COLOURS = {"route": "var(--r1)", "gate": "var(--r4)", "stop": "var(--r2)", "proof": "var(--r3)"}


def inline(text):
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)


def markdown(text):
    """Enough markdown for specs and reports: headings, bullets, code blocks, tables, paragraphs."""
    out, in_code, in_list, in_table = [], False, False, False
    for line in text.splitlines():
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
            out.append("<li>{}</li>".format(inline(bullet.group(1))))
        elif row:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", c) for c in cells):
                continue
            if not in_table:
                out.append("<table>")
                in_table = True
            out.append("<tr>{}</tr>".format("".join("<td>{}</td>".format(inline(c)) for c in cells)))
        elif line.strip():
            out.append("<p>{}</p>".format(inline(line)))
    return "\n".join(out + (["</ul>"] if in_list else []) + (["</table>"] if in_table else []) + (["</pre>"] if in_code else []))


def terminal(text):
    lines = []
    for line in text.splitlines():
        escaped = html.escape(line)
        if line.startswith("$ "):
            escaped = '<span class="cmd">{}</span>'.format(escaped)
        elif re.search(r"waiting|Waiting for|gate", line):
            escaped = '<span class="hold">{}</span>'.format(escaped)
        elif re.search(r"approved|opened|Posted|OK\b|PASS|passed|done\b|accepted", line):
            escaped = '<span class="good">{}</span>'.format(escaped)
        elif line.startswith(("==", "ITEM")):
            escaped = '<span class="dim">{}</span>'.format(escaped)
        lines.append(escaped)
    return "\n".join(lines)


def excerpt(name, start=None, end=None, lines=None):
    text = (CAPTURES / name).read_text()
    if start:
        text = text[text.index(start):]
    if end and end in text:
        text = text[:text.index(end)]
    return "\n".join(text.splitlines()[:lines]) if lines else text


def body_of(scene):
    kind = scene["kind"]
    colour = COLOURS.get(scene.get("part_kind", "route"), "var(--r1)")
    if kind == "card":
        return ('<div class="card" style="--c:{}"><div class="bars"><i style="background:var(--r1)"></i><i style="background:var(--r2)"></i>'
                '<i style="background:var(--r3)"></i><i style="background:var(--r4)"></i></div>'
                '<div class="kicker">{}</div><h1>{}</h1><p>{}</p></div>').format(
                    colour, html.escape(scene.get("kicker", "")), html.escape(scene["title"]), html.escape(scene.get("say", "")))
    bar = '<div class="bar" style="--c:{}"><span class="part">{}</span><span class="say">{}</span></div>'.format(
        colour, html.escape(scene["part"]), html.escape(scene["say"]))
    if kind == "terminal":
        inner = '<div class="term"><div class="top"><s></s><s></s><s></s><span>{}</span></div><pre>{}</pre></div>'.format(
            html.escape(scene.get("where", "terminal")), terminal(scene["text"]))
    elif kind == "doc":
        inner = '<div class="doc">{}</div>'.format(markdown(scene["text"]))
    else:
        inner = '<div class="shot"><img src="../shots/{}" style="margin-top:-{}px"></div>'.format(scene["image"], scene.get("offset", 0))
    return bar + '<div class="stage">{}</div>'.format(inner)


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
:root { --bg: #f2f4f7; --paper: #fff; --ink: #0f1b2d; --muted: #5d6b7e; --line: #d6dce5; --accent: #1f5fd0; --code: #0f1b2d; --code-ink: #e6ecf5; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg: #0b121c; --paper: #121c2a; --ink: #e8eef7; --muted: #92a0b3; --line: #26344a; --accent: #6aa0ff; --code: #070c13; color-scheme: dark; } }
:root[data-theme="dark"] { --bg: #0b121c; --paper: #121c2a; --ink: #e8eef7; --muted: #92a0b3; --line: #26344a; --accent: #6aa0ff; --code: #070c13; color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 17px/1.55 "Barlow", "Helvetica Neue", Arial, sans-serif; }
.wrap { max-width: 980px; margin: 0 auto; padding-inline: 20px; padding-block: 40px 80px; display: grid; gap: 44px; }
h1 { margin: 0; font: 700 clamp(40px, 7vw, 76px)/0.96 "Barlow Condensed", "Arial Narrow", Arial, sans-serif; text-transform: uppercase; text-wrap: balance; }
h2 { margin: 0; font: 700 34px/1 "Barlow Condensed", Arial, sans-serif; text-transform: uppercase; text-wrap: balance; }
p { margin: 0; max-width: 66ch; } a { color: var(--accent); }
header { display: grid; gap: 16px; } header p { font-size: 20px; color: var(--muted); }
video, figure img { width: 100%; display: block; border-radius: 12px; border: 1px solid var(--line); background: #0b121c; }
section { display: grid; gap: 14px; min-width: 0; }
.part { font: 700 14px "Barlow Condensed", Arial, sans-serif; letter-spacing: .12em; text-transform: uppercase; color: var(--accent); }
figure { margin: 0; display: grid; gap: 8px; } figcaption { font-size: 14px; color: var(--muted); }
.how { background: var(--paper); border: 1px solid var(--line); border-radius: 12px; padding: 16px 18px; display: grid; gap: 8px; min-width: 0; }
.how b { font: 700 16px "Barlow Condensed", Arial, sans-serif; letter-spacing: .08em; text-transform: uppercase; }
pre { margin: 0; background: var(--code); color: var(--code-ink); border-radius: 8px; padding: 12px 14px; font: 13.5px/1.6 "IBM Plex Mono", Menlo, monospace; white-space: pre-wrap; overflow-wrap: anywhere; }
.facts { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 200px), 1fr)); gap: 12px; }
.facts div { background: var(--paper); border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px; }
.facts b { display: block; font: 700 30px/1 "Barlow Condensed", Arial, sans-serif; } .facts span { font-size: 14px; color: var(--muted); }
ul { margin: 0; padding-left: 20px; display: grid; gap: 4px; max-width: 66ch; }
footer { color: var(--muted); font-size: 14px; }
"""


def page(scenes, facts, links):
    parts, current = [], None
    for scene in scenes:
        if scene["kind"] == "card":
            current = {"title": scene["title"], "kicker": scene.get("kicker", ""), "text": scene.get("explain", scene.get("say", "")),
                       "how": scene.get("how"), "figures": []}
            parts.append(current)
        elif current is not None:
            current["figures"].append(scene)
    sections = []
    for part in parts:
        figures = "".join('<figure><img src="frames/{}" alt="{}" loading="lazy"><figcaption>{}</figcaption></figure>'.format(
            f["frame"], html.escape(f["say"]), html.escape(f.get("note", f["say"]))) for f in part["figures"])
        how = '<div class="how"><b>Do this yourself</b>{}</div>'.format(part["how"]) if part["how"] else ""
        sections.append('<section><span class="part">{}</span><h2>{}</h2><p>{}</p>{}{}</section>'.format(
            html.escape(part["kicker"]), html.escape(part["title"]), part["text"], figures, how))
    fact_html = "".join("<div><b>{}</b><span>{}</span></div>".format(html.escape(str(v)), html.escape(k)) for k, v in facts)
    link_html = "".join('<li><a href="{}">{}</a></li>'.format(html.escape(u), html.escape(t)) for t, u in links)
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            "<title>Factory Demo</title>{}<style>{}</style></head><body><div class=\"wrap\">"
            "<header><span class=\"part\">Software factory · a real run, start to finish</span><h1>Two repositories, two routes, one factory</h1>"
            "<p>Two GitHub issues went in. Agents wrote the requirements, stopped at each gate for approval, built the change with a maker and a checker, "
            "proved it with evidence, and opened pull requests. Everything below is from that run.</p>"
            '<video src="factory-demo.mp4" controls preload="metadata" poster="frames/{}"></video></header>'
            '<div class="facts">{}</div>{}'
            "<section><h2>See it for yourself</h2><ul>{}</ul></section>"
            "<footer>Frames and video are built by docs/demo/build.py from the captured output of the run. Nothing is mocked.</footer>"
            "</div></body></html>\n").format(FONTS, PAGE_CSS, scenes[0]["frame"], fact_html, "".join(sections), link_html)


def main():
    story = json.loads((HERE / "story.json").read_text())
    scenes = story["scenes"]
    for scene in scenes:
        if "file" in scene:
            scene["text"] = excerpt(scene["file"], scene.get("start"), scene.get("end"), scene.get("lines"))
    draw(scenes)
    out = video(scenes)
    (HERE / "index.html").write_text(page(scenes, story["facts"], story["links"]))
    seconds = sum(s.get("seconds", 6) for s in scenes)
    print("{} scenes, {}:{:02d}  {}  {:.1f} MB".format(len(scenes), seconds // 60, seconds % 60, out.name, out.stat().st_size / 1e6))


if __name__ == "__main__":
    main()
