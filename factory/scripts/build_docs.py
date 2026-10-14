#!/usr/bin/env python3
"""Render docs/index.html, the product page for the factory.

The pipeline map is drawn from factories/*/factory.json, so the page cannot
drift from the sample definitions. Run it after changing a sample:

    python3 factory/scripts/build_docs.py
"""

import html
import json
from pathlib import Path

HOME = Path(__file__).resolve().parent.parent.parent
REPO_URL = "https://github.com/sanjeev23oct/software-factory"
ROUTES = [  # sample, display name, what it is for, colour token
    ("spec-driven", "Spec-driven", "Full-stack features", "r1"),
    ("backend-api", "Backend API", "APIs and databases", "r2"),
    ("ui-app", "UI app", "Screens and forms", "r3"),
    ("bugfix", "Bug fix", "Bug reports", "r4"),
]
STARTS = {"file": "a file", "github": "GitHub", "gitlab": "GitLab", "jira": "Jira"}
# Where each stage sits on the map, so the same stop lines up across routes.
COLUMN = {"requirements": 1, "reproduce": 1, "approve-requirements": 2, "design": 3, "visual-spec": 3,
          "approve-design": 4, "tasks": 5, "build": 6, "fix": 6, "verify": 7, "review": 8,
          "approve-screens": 9, "approve-fix": 9, "merge-request": 10}
LABEL = {"requirements": "Requirements", "reproduce": "Reproduce", "design": "Design", "visual-spec": "Visual spec",
         "tasks": "Tasks", "build": "Build", "fix": "Fix", "verify": "Verify", "review": "Review",
         "merge-request": "Merge request"}
X0, STEP, Y0, ROW = 214, 86, 64, 96


def route(sample):
    """The stops of one sample factory: (column, label, kind) with kind in stop, optional, you, planned."""
    definition = json.loads((HOME / "factories" / sample / "factory.json").read_text())
    stops = [(0, "Intake", "stop")]
    for stage in definition["stages"]:
        name = stage["id"]
        if stage["by"] == "human":
            stops.append((COLUMN[name], name.replace("approve-", ""), "you"))
        elif name == "merge-request":
            continue
        elif name == "pull-request":
            stops.append((COLUMN["merge-request"], "Pull request", "optional"))
        elif name in LABEL:
            stops.append((COLUMN[name], LABEL[name], "optional" if stage.get("optional") else "stop"))
    return definition, stops


def route_map():
    parts = []
    for row, (sample, name, purpose, colour) in enumerate(ROUTES):
        definition, stops = route(sample)
        y = Y0 + row * ROW
        xs = [X0 + col * STEP for col, _, _ in stops]
        solid_end = max(x for x, (_, _, kind) in zip(xs, stops) if kind != "planned")
        g = ['<g class="route {}" data-route="{}">'.format(colour, sample),
             '<text class="rname" x="0" y="{}">{}</text>'.format(y - 2, html.escape(name)),
             '<text class="rfrom" x="0" y="{}">from {}</text>'.format(y + 15, STARTS[definition["source"]["type"]]),
             '<path class="rail" d="M{} {}H{}"/>'.format(xs[0], y, solid_end)]
        if xs[-1] > solid_end:
            g.append('<path class="rail later" d="M{} {}H{}"/>'.format(solid_end, y, xs[-1]))
        for x, (_, label, kind) in zip(xs, stops):
            if kind == "you":
                g.append('<circle class="you" cx="{}" cy="{}" r="12"/>'.format(x, y))
                g.append('<path class="person" d="M{0} {1}a3 3 0 1 0 0.01 0M{2} {3}c1-4 9-4 10 0" />'.format(x, y - 7, x - 5, y + 6))
                g.append('<text class="slabel strong" x="{}" y="{}">Gate</text>'.format(x, y + 31))
                g.append('<text class="slabel" x="{}" y="{}">{}</text>'.format(x, y + 45, html.escape(label)))
            elif kind == "planned":
                g.append('<rect class="end" x="{}" y="{}" width="14" height="14" rx="2"/>'.format(x - 7, y - 7))
                g.append('<text class="slabel" x="{}" y="{}">{}</text>'.format(x, y + 31, html.escape(label)))
                g.append('<text class="slabel faint" x="{}" y="{}">planned</text>'.format(x, y + 45))
            else:
                g.append('<circle class="{}" cx="{}" cy="{}" r="7"/>'.format("stop opt" if kind == "optional" else "stop", x, y))
                g.append('<text class="slabel" x="{}" y="{}">{}</text>'.format(x, y + 31, html.escape(label)))
                if kind == "optional":
                    g.append('<text class="slabel faint" x="{}" y="{}">optional</text>'.format(x, y + 45))
        g.append("</g>")
        parts.append("".join(g))
    y = Y0 + len(ROUTES) * ROW
    mine = ['<g class="route mine" data-route="yours">', '<text class="rname" x="0" y="{}">Your pipeline</text>'.format(y - 2),
            '<text class="rfrom" x="0" y="{}">from any tracker</text>'.format(y + 15),
            '<path class="rail later" d="M{} {}H{}"/>'.format(X0, y, X0 + 10 * STEP)]
    for col in (0, 1, 3, 5, 6, 7, 10):
        mine.append('<circle class="stop opt" cx="{}" cy="{}" r="7"/>'.format(X0 + col * STEP, y))
    for col in (2, 9):
        mine.append('<circle class="you opt" cx="{}" cy="{}" r="12"/>'.format(X0 + col * STEP, y))
    for col, text, strong in ((2, "your gates", True), (5, "any stops, in any order", False), (10, "any kind of work", False)):
        mine.append('<text class="slabel{}" x="{}" y="{}">{}</text>'.format(" strong" if strong else "", X0 + col * STEP, y + 31, text))
    parts.append("".join(mine) + "</g>")
    height = Y0 + len(ROUTES) * ROW + 62
    return ('<svg class="map" viewBox="0 0 1124 {}" role="img" aria-label="Map of the four sample pipelines, '
            'showing each stage as a stage and each human approval as a ringed stage">{}</svg>').format(height, "".join(parts))


def route_cards():
    cards = []
    for sample, name, purpose, colour in ROUTES:
        definition, stops = route(sample)
        yours = [label for _, label, kind in stops if kind == "you"]
        work = sum(1 for _, _, kind in stops if kind in ("stop", "optional")) - 1
        cards.append(
            '<button type="button" class="rcard {}" data-route="{}" aria-pressed="false"><span class="swatch"></span>'
            '<b>{}</b><span>{}</span><span class="meta">from {} · {} stages · gates: {}</span></button>'.format(
                colour, sample, name, purpose, STARTS[definition["source"]["type"]], work, ", ".join(yours)))
    return "".join(cards)


STYLE = """
/* Layout: the route map is the page. A short headline above it, a row of route cards under it, then three compact bands. */
:root {
  --bg: #f2f4f7; --paper: #ffffff; --ink: #0f1b2d; --muted: #5d6b7e; --line: #d6dce5;
  --r1: #1f5fd0; --r2: #12905a; --r3: #b3348c; --r4: #d96a12; --ok: #12905a; --code: #0f1b2d; --code-ink: #e6ecf5;
  --display: "Barlow Condensed", "Arial Narrow", Arial, sans-serif;
  --body: "Barlow", "Helvetica Neue", Arial, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #0b121c; --paper: #121c2a; --ink: #e8eef7; --muted: #92a0b3; --line: #26344a;
    --r1: #6aa0ff; --r2: #4fd09a; --r3: #ef7cc9; --r4: #ffa154; --ok: #4fd09a; --code: #070c13;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #0b121c; --paper: #121c2a; --ink: #e8eef7; --muted: #92a0b3; --line: #26344a;
  --r1: #6aa0ff; --r2: #4fd09a; --r3: #ef7cc9; --r4: #ffa154; --ok: #4fd09a; --code: #070c13;
  color-scheme: dark;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 17px/1.5 var(--body); }
.wrap { max-width: 1180px; margin: 0 auto; padding-inline: 20px; }
h1, h2, h3, p { margin: 0; }
h1 { font: 700 clamp(44px, 8.4vw, 92px)/0.94 var(--display); letter-spacing: -0.01em; text-transform: uppercase; text-wrap: balance; }
h2 { font: 700 clamp(30px, 4.6vw, 46px)/1 var(--display); text-transform: uppercase; text-wrap: balance; }
h3 { font: 600 19px/1.25 var(--body); }
a { color: inherit; }
a:focus-visible, button:focus-visible { outline: 3px solid var(--r1); outline-offset: 3px; }
.r1 { --c: var(--r1); } .r2 { --c: var(--r2); } .r3 { --c: var(--r3); } .r4 { --c: var(--r4); }

nav { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding-block: 20px; }
.brand { font: 700 22px var(--display); text-transform: uppercase; letter-spacing: 0.02em; text-decoration: none; display: flex; align-items: center; gap: 10px; }
.brand i { display: flex; gap: 3px; } .brand i b { width: 5px; height: 18px; border-radius: 3px; }
.brand i b:nth-child(1) { background: var(--r1); } .brand i b:nth-child(2) { background: var(--r2); }
.brand i b:nth-child(3) { background: var(--r3); } .brand i b:nth-child(4) { background: var(--r4); }
nav .links { display: flex; gap: 24px; font-size: 16px; }
nav .links a { text-decoration: none; color: var(--muted); } nav .links a:hover { color: var(--ink); }

.hero { padding-block: 36px 28px; display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); gap: 20px 40px; align-items: end; }
.hero p { font-size: 20px; color: var(--muted); max-width: 30ch; }
.cta { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }
.btn { font: 600 16px var(--body); padding: 12px 20px; border-radius: 99px; text-decoration: none; border: 2px solid var(--ink); }
.btn.solid { background: var(--ink); color: var(--bg); }

.board { background: var(--paper); border-radius: 18px; border: 1px solid var(--line); padding: 22px 22px 18px; display: grid; gap: 16px; }
.board-top { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px 24px; }
.board-top h2 { font-size: 26px; }
.key { display: flex; flex-wrap: wrap; gap: 8px 20px; font-size: 14px; color: var(--muted); }
.key span { display: flex; align-items: center; gap: 7px; }
.key svg { width: 26px; height: 26px; }
.scroll { overflow-x: auto; }
.map { display: block; width: 100%; min-width: 940px; height: auto; }
.map text { font-family: var(--body); fill: var(--ink); }
.rname { font: 700 21px var(--display); text-transform: uppercase; fill: var(--c) !important; }
.rfrom { font-size: 12px; fill: var(--muted) !important; }
.rail { fill: none; stroke: var(--c); stroke-width: 7; stroke-linecap: round; }
.rail.later { stroke-width: 4; stroke-dasharray: 2 9; }
.stop { fill: var(--paper); stroke: var(--c); stroke-width: 4; }
.stop.opt { stroke-dasharray: 3 3; stroke-width: 3; }
.you { fill: var(--paper); stroke: var(--ink); stroke-width: 4; }
.person { fill: none; stroke: var(--ink); stroke-width: 1.8; stroke-linecap: round; }
.mine { --c: var(--muted); } .you.opt { stroke: var(--muted); stroke-dasharray: 4 4; stroke-width: 3; }
.end { fill: var(--paper); stroke: var(--c); stroke-width: 3; stroke-dasharray: 3 3; }
.slabel { font-size: 12px; text-anchor: middle; }
.slabel.strong { font-weight: 600; } .slabel.faint { fill: var(--muted) !important; font-size: 11px; }
.route { transition: opacity .2s; }
.map[data-pick] .route { opacity: 0.16; }
.map[data-pick="spec-driven"] .route[data-route="spec-driven"], .map[data-pick="backend-api"] .route[data-route="backend-api"],
.map[data-pick="ui-app"] .route[data-route="ui-app"], .map[data-pick="bugfix"] .route[data-route="bugfix"] { opacity: 1; }
.rcards { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.rcard { text-align: left; font: inherit; color: inherit; cursor: pointer; background: var(--bg); border: 2px solid transparent; border-radius: 12px;
  padding: 14px 14px 14px 18px; display: grid; gap: 2px; position: relative; min-width: 0; }
.rcard .swatch { position: absolute; left: 0; top: 14px; bottom: 14px; width: 6px; border-radius: 0 4px 4px 0; background: var(--c); }
.rcard b { font: 700 22px/1.1 var(--display); text-transform: uppercase; color: var(--c); }
.rcard span { font-size: 15px; } .rcard .meta { font-size: 13px; color: var(--muted); margin-top: 4px; }
.rcard[aria-pressed="true"] { border-color: var(--c); background: var(--paper); }
.hint { font-size: 13px; color: var(--muted); }

section { padding-block: 64px 0; display: grid; gap: 24px; }
.pillars { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
.pillar { background: var(--paper); border: 1px solid var(--line); border-top: 6px solid var(--c); border-radius: 14px; padding: 18px 20px 20px; display: grid; gap: 6px; align-content: start; }
.pillar span { font: 700 15px var(--display); color: var(--c); letter-spacing: 0.06em; }
.pillar h3 { font: 700 26px/1.05 var(--display); text-transform: uppercase; }
.pillar p { color: var(--muted); font-size: 16px; }
.eyebrow { display: inline-block; font: 600 14px var(--body); letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); margin-bottom: 14px; }
.duo { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 28px 44px; align-items: center; }
.points { display: grid; gap: 18px; }
.point { display: grid; grid-template-columns: 14px minmax(0, 1fr); gap: 2px 14px; }
.point i { grid-row: span 2; width: 14px; height: 14px; border-radius: 50%; border: 4px solid var(--c); margin-top: 5px; }
.point p { grid-column: 2; color: var(--muted); font-size: 16px; }

/* evidence, drawn as a ticket */
.ticket { background: var(--paper); border-radius: 14px; border: 1px solid var(--line); font: 13px var(--mono); min-width: 0; overflow: hidden; }
.ticket-top { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 6px 14px; padding: 14px 18px; border-bottom: 2px dashed var(--line); }
.ticket-top b { color: var(--ok); }
.ticket-scroll { overflow-x: auto; }
.ticket table { width: 100%; border-collapse: collapse; }
.ticket td, .ticket th { padding: 8px 18px; text-align: left; white-space: nowrap; }
.ticket th { font-weight: 500; font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); }
.ticket td:last-child { color: var(--ok); font-weight: 600; }
.ticket-foot { padding: 12px 18px; border-top: 2px dashed var(--line); color: var(--muted); font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; }

.code { background: var(--code); color: var(--code-ink); border-radius: 14px; padding: 20px; font: 13px/1.7 var(--mono); overflow-x: auto; margin: 0; }
.code .k1 { color: #8db4ff; } .code .k2 { color: #ffb37a; } .code .c { color: #7f8da3; }

.steps { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
.step { background: var(--paper); border: 1px solid var(--line); border-radius: 14px; padding: 20px; display: grid; gap: 10px; align-content: start; min-width: 0; }
.step .n { font: 700 34px/1 var(--display); color: var(--c); }
.step p { color: var(--muted); font-size: 15px; }
.cmd { position: relative; min-width: 0; }
.cmd pre { margin: 0; background: var(--code); color: var(--code-ink); border-radius: 10px; padding: 36px 14px 14px; font: 12.5px/1.65 var(--mono); white-space: pre-wrap; overflow-wrap: anywhere; }
.cmd button { position: absolute; top: 8px; right: 8px; font: 600 11px var(--body); background: #24334a; color: #e6ecf5; border: 0; border-radius: 99px; padding: 5px 10px; cursor: pointer; }
.now { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.now div { background: var(--paper); border: 1px solid var(--line); border-radius: 14px; padding: 20px; display: grid; gap: 10px; align-content: start; }
.now h3 { font: 700 22px var(--display); text-transform: uppercase; }
.now ul { margin: 0; padding: 0; list-style: none; display: grid; gap: 6px; font-size: 16px; }
.now li { display: flex; gap: 10px; align-items: baseline; }
.now li::before { content: ""; flex: none; width: 10px; height: 10px; border-radius: 50%; background: var(--ok); }
.now .later li::before { background: transparent; border: 2px dashed var(--muted); }
footer { margin-top: 64px; padding-block: 26px; border-top: 1px solid var(--line); display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px 20px; font-size: 15px; color: var(--muted); }

@media (max-width: 880px) {
  nav .links a:not(.keep) { display: none; }
  .hero, .duo, .steps, .now, .pillars { grid-template-columns: minmax(0, 1fr); }
  .rcards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  section { padding-top: 48px; }
  .board { padding: 16px; border-radius: 14px; }
}
@media (max-width: 460px) { .rcards { grid-template-columns: minmax(0, 1fr); } }
@media (prefers-reduced-motion: reduce) { .route { transition: none; } }
"""

FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;600'
         '&family=Barlow+Condensed:wght@600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">')

SCRIPT = """
<script>
(function () {
  var map = document.querySelector('.map'), cards = document.querySelectorAll('.rcard');
  function pick(id) {
    var same = map.getAttribute('data-pick') === id;
    if (same) { map.removeAttribute('data-pick'); } else { map.setAttribute('data-pick', id); }
    cards.forEach(function (c) { c.setAttribute('aria-pressed', !same && c.dataset.route === id ? 'true' : 'false'); });
  }
  cards.forEach(function (c) { c.addEventListener('click', function () { pick(c.dataset.route); }); });
  map.querySelectorAll('.route').forEach(function (g) {
    g.style.cursor = 'pointer';
    g.addEventListener('click', function () { pick(g.getAttribute('data-route')); });
  });
  document.querySelectorAll('.cmd button').forEach(function (button) {
    button.addEventListener('click', function () {
      var pre = button.parentNode.querySelector('pre');
      var done = function () { button.textContent = 'Copied'; setTimeout(function () { button.textContent = 'Copy'; }, 1400); };
      var select = function () { var r = document.createRange(); r.selectNodeContents(pre); var s = getSelection(); s.removeAllRanges(); s.addRange(r); };
      try { navigator.clipboard.writeText(pre.textContent).then(done, select); } catch (e) { select(); }
    });
  });
})();
</script>
"""

KEY = (
    '<span><svg viewBox="0 0 26 26"><path d="M0 13H26" stroke="var(--muted)" stroke-width="5"/>'
    '<circle cx="13" cy="13" r="6" fill="var(--paper)" stroke="var(--muted)" stroke-width="3.5"/></svg>Stage: work agents complete</span>'
    '<span><svg viewBox="0 0 26 26"><path d="M0 13H26" stroke="var(--muted)" stroke-width="5"/>'
    '<circle cx="13" cy="13" r="10" fill="var(--paper)" stroke="var(--ink)" stroke-width="3.5"/></svg>Gate: a person approves</span>'
    '<span><svg viewBox="0 0 26 26"><path d="M0 13H26" stroke="var(--muted)" stroke-width="5"/>'
    '<circle cx="13" cy="13" r="6" fill="var(--paper)" stroke="var(--muted)" stroke-width="3" stroke-dasharray="3 3"/></svg>Optional</span>'
)


def cmd(text):
    return '<div class="cmd"><pre>{}</pre><button type="button">Copy</button></div>'.format(html.escape(text))


def body():
    return """
<div class="wrap">
<nav><a class="brand" href="#top"><i><b></b><b></b><b></b><b></b></i>Software Factory</a>
  <div class="links"><a href="#routes">Pipelines</a><a href="#pillars">Pillars</a><a href="#proof">Proof</a><a href="#start">Get started</a><a class="keep" href="%(repo)s">GitHub</a></div></nav>

<header class="hero" id="top">
  <div><span class="eyebrow">A software factory for any team</span><h1>Define the pipeline. Agents run it.</h1></div>
  <div><p>Lay out the stages between a request and a merge. Set gates where a person must approve. The factory runs the rest.</p>
    <div class="cta"><a class="btn solid" href="#start">Get started</a><a class="btn" href="%(repo)s">GitHub</a></div></div>
</header>

<div class="board" id="routes">
  <div class="board-top"><h2>Example pipelines</h2><div class="key">%(key)s</div></div>
  <div class="scroll">%(map)s</div>
  <div class="rcards">%(cards)s</div>
  <span class="hint">These four are examples. The factory is not tied to UI, backend, or any stack: a pipeline is whatever stages and gates your work needs. Select one to trace it.</span>
</div>

<section id="pillars">
  <h2>What makes it a factory</h2>
  <div class="pillars">
    <div class="pillar r1"><span>01</span><h3>One line</h3><p>Every request travels the same defined pipeline. No improvising.</p></div>
    <div class="pillar r2"><span>02</span><h3>Gates</h3><p>The line stops at named points until a person approves.</p></div>
    <div class="pillar r3"><span>03</span><h3>Standard work</h3><p>Each stage follows a written skill, so the work is done the same way each time.</p></div>
    <div class="pillar r4"><span>04</span><h3>Proof at every stage</h3><p>Work moves on only with evidence that it passed its checks.</p></div>
    <div class="pillar r1"><span>05</span><h3>A full record</h3><p>Every move is logged: what ran, what passed, when each gate opened.</p></div>
    <div class="pillar r2"><span>06</span><h3>Open by design</h3><p>Any tracker, any stack, any coding agent. Pipelines and skills are plain files.</p></div>
  </div>
</section>

<section id="yours">
  <div class="duo">
    <div class="points">
      <h2>Draw your own pipeline</h2>
      <div class="point r1"><i></i><h3>Add, remove or reorder stages</h3><p>A pipeline is a short list in one file.</p></div>
      <div class="point r2"><i></i><h3>Put gates where you want them</h3><p>Before design, after the build, or only at the end.</p></div>
      <div class="point r3"><i></i><h3>Start from your tracker</h3><p>GitHub, GitLab, Jira, or a plain file.</p></div>
      <div class="point r4"><i></i><h3>Teach each stage your way</h3><p>Every stage follows a skill you can rewrite.</p></div>
    </div>
    <pre class="code"><span class="c">// targets/shop/factory.json</span>
<span class="k1">"source"</span>: { "type": "github", "repo": "acme/shop" },
<span class="k1">"stages"</span>: [
  { "id": "requirements" },
  { "id": <span class="k2">"approve-requirements"</span>, "by": <span class="k2">"human"</span> },
  { "id": "design", "optional": true },
  { "id": "tasks" },
  { "id": "build" },
  { "id": "verify" }
]</pre>
  </div>
</section>

<section id="proof">
  <div class="duo">
    <div class="ticket">
      <div class="ticket-top"><span>BUILD · backend gate</span><b>PASS 5/5</b></div>
      <div class="ticket-scroll"><table>
        <tr><th>Check</th><th>Expected</th><th>Found</th><th></th></tr>
        <tr><td>build errors</td><td>0</td><td>0</td><td>&#10003;</td></tr>
        <tr><td>POST /api/orders/export</td><td>201</td><td>201</td><td>&#10003;</td></tr>
        <tr><td>export without permission</td><td>403</td><td>403</td><td>&#10003;</td></tr>
        <tr><td>raw SQL in controllers</td><td>0</td><td>0</td><td>&#10003;</td></tr>
        <tr><td>integration tests</td><td>12 passed</td><td>12 passed</td><td>&#10003;</td></tr>
      </table></div>
      <div class="ticket-foot">Example ticket, for illustration</div>
    </div>
    <div class="points">
      <h2>Every stage stamps a ticket</h2>
      <div class="point r2"><i></i><h3>One builds, another checks</h3><p>The agent that did the work never marks its own homework.</p></div>
      <div class="point r2"><i></i><h3>Expected against found</h3><p>Each check is written down with its result.</p></div>
      <div class="point r2"><i></i><h3>No ticket, no progress</h3><p>Unproven work is sent back to the stage that did it.</p></div>
    </div>
  </div>
</section>

<section id="start">
  <h2>On the road in three commands</h2>
  <div class="steps">
    <div class="step r1"><span class="n">1</span><h3>Pick a pipeline</h3><p>Copy the nearest sample and point it at your repository.</p>%(c1)s</div>
    <div class="step r3"><span class="n">2</span><h3>Redraw it</h3><p>Set your tracker, your rules and your tests. Move the gates.</p>%(c2)s</div>
    <div class="step r4"><span class="n">3</span><h3>Send one issue</h3><p>It runs until it reaches your first gate.</p>%(c3)s</div>
  </div>
</section>

<section>
  <h2>Where it stands</h2>
  <div class="now">
    <div><h3>Running today</h3><ul><li>Example pipelines to start from, or a blank one</li><li>Issues from GitHub, GitLab, or a file</li>
      <li>A background job that picks up work unattended</li><li>Gates you approve from a page</li><li>Unproven work sent back automatically</li>
      <li>Pull and merge requests opened for you to merge</li><li>Pull requests reviewed: process first, then code</li>
      <li>An editor for pipelines and review rules</li><li>Built-in runner for Claude Code; any agent can take a stage by hand-off</li></ul></div>
    <div class="later"><h3>Not built yet</h3><ul><li>Approving a gate from the tracker itself</li><li>Commenting progress on the issue</li>
      <li>Jira, tested against a real instance</li><li>Built-in runners for other coding agents</li><li>A host that is always on: a laptop that sleeps stops the line</li></ul></div>
  </div>
</section>

<footer><span>Software Factory · any tracker, any stack, any agent</span><a href="%(repo)s">%(repo_short)s</a></footer>
</div>
""" % {
        "repo": REPO_URL, "repo_short": REPO_URL.replace("https://", ""), "key": KEY,
        "map": route_map(), "cards": route_cards(),
        "c1": cmd("python3 factory/flow.py init shop \\\n  --sample backend-api \\\n  --repo ~/code/shop"),
        "c2": cmd("python3 factory/flow.py --target shop show\npython3 factory/flow.py --target shop validate"),
        "c3": cmd("python3 factory/flow.py --target shop \\\n  start --issue 42\npython3 factory/flow.py --target shop run"),
    }


def main():
    head = "<title>Software Factory</title>{}<style>{}</style>".format(FONTS, STYLE)
    docs = HOME / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">{}</head><body>{}{}</body></html>\n'.format(
            head, body(), SCRIPT))
    print(docs / "index.html")


if __name__ == "__main__":
    main()
