#!/usr/bin/env python3
"""Render docs/index.html, the product page for the factory.

The line shown for each sample factory is drawn from factories/*/factory.json,
so the page cannot drift from the definitions. Run it after changing a sample:

    python3 factory/scripts/build_docs.py
"""

import html
import json
from pathlib import Path

HOME = Path(__file__).resolve().parent.parent.parent
REPO_URL = "https://github.com/sanjeev23oct/software-factory"
ORDER = ["spec-driven", "backend-api", "ui-app", "bugfix"]
TAB = {"spec-driven": "spec-driven", "backend-api": "backend api", "ui-app": "ui app", "bugfix": "bug fix"}
ISSUE = {"spec-driven": ("FILE", "export-orders.md", "export orders as csv"),
         "backend-api": ("GITHUB", "#42", "rate-limit headers on the public api"),
         "ui-app": ("GITLAB", "#118", "bulk-edit drawer for equipment"),
         "bugfix": ("JIRA", "SHOP-311", "order total rounds the wrong way")}
NAMES = {"requirements": "Requirements", "design": "Design", "visual-spec": "Visual spec", "tasks": "Tasks",
         "build": "Build", "verify": "Verify", "reproduce": "Reproduce", "fix": "Fix", "review": "Review"}
NOTES = {"requirements": "what to build, as testable criteria", "design": "data, api and screens, spelled out",
         "visual-spec": "every screen and state pinned down", "tasks": "small tasks, a skill named on each",
         "build": "maker builds, checker proves it", "verify": "build, lint and tests", "reproduce": "a failing test first",
         "fix": "the root cause, nothing more", "review": "an independent read of the diff"}
GATES = {"approve-requirements": "review the requirements", "approve-design": "review the design",
         "approve-screens": "review the screens", "approve-fix": "review the fix"}


def line(name):
    """The stages a person cares about, with the points where the line stops for them."""
    definition = json.loads((HOME / "factories" / name / "factory.json").read_text())
    source, ref, title = ISSUE[name]
    nodes = [{"name": "Intake", "note": "from " + source.lower()}]
    for stage in definition["stages"]:
        if stage.get("intake"):
            continue
        if stage["by"] == "human":
            nodes[-1]["gate"] = GATES[stage["id"]]
        elif stage["id"] == "merge-request":
            nodes.append({"name": "Merge request", "note": "opened for you", "planned": True, "gate": "merge is yours"})
        elif stage["id"] in NAMES:
            nodes.append({"name": NAMES[stage["id"]], "note": NOTES[stage["id"]], "optional": bool(stage.get("optional"))})
    return {"id": name, "tab": TAB[name], "source": source, "ref": ref, "title": title, "nodes": nodes}


STYLE = """
/* Layout: a technical drawing. One figure, the line, carries the page; everything else is a short numbered note beside a figure. */
:root {
  --bg: #fafbf9; --dot: #dfe3de; --surface: #ffffff; --ink: #14181b; --muted: #6a7378; --line: #cfd5d1; --rule: #14181b;
  --accent: #d9481c; --accent-soft: #fbe6dd; --ok: #1f7a55; --code: #14181b; --code-ink: #e8ece9; --code-dim: #8b979d;
  --display: "Schibsted Grotesk", "Helvetica Neue", Arial, sans-serif;
  --mono: "JetBrains Mono", ui-monospace, Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #0e1113; --dot: #20262a; --surface: #14181b; --ink: #e9edea; --muted: #8b979d; --line: #2b3338; --rule: #e9edea;
    --accent: #ff7a4d; --accent-soft: #3a1c10; --ok: #5fc898; --code: #080a0b;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #0e1113; --dot: #20262a; --surface: #14181b; --ink: #e9edea; --muted: #8b979d; --line: #2b3338; --rule: #e9edea;
  --accent: #ff7a4d; --accent-soft: #3a1c10; --ok: #5fc898; --code: #080a0b;
  color-scheme: dark;
}
* { box-sizing: border-box; }
body { margin: 0; color: var(--ink); font: 14px/1.6 var(--mono);
  background: radial-gradient(var(--dot) 1px, transparent 1px) 0 0 / 22px 22px, var(--bg); }
.wrap { max-width: 1140px; margin: 0 auto; padding-inline: 20px; }
h1, h2, h3, p { margin: 0; }
h1 { font: 600 clamp(36px, 6.6vw, 68px)/1.02 var(--display); letter-spacing: -0.03em; text-wrap: balance; max-width: 15ch; }
h2 { font: 600 clamp(26px, 4vw, 38px)/1.1 var(--display); letter-spacing: -0.02em; text-wrap: balance; }
h3 { font: 600 19px/1.25 var(--display); letter-spacing: -0.01em; }
a { color: inherit; }
a:focus-visible, button:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
.tag { font: 500 11px/1.3 var(--mono); letter-spacing: 0.1em; text-transform: uppercase; }
.tag b { font-weight: 700; } .tag i { font-style: normal; color: var(--muted); }
.dim { color: var(--muted); }

nav { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding-block: 18px; border-bottom: 1px solid var(--line); }
.brand { font: 600 17px var(--display); text-decoration: none; display: flex; align-items: center; gap: 9px; }
.brand span { width: 20px; height: 20px; border: 1.5px solid var(--ink); display: grid; place-items: center; font: 700 11px var(--mono); border-radius: 50%; }
nav div { display: flex; gap: 22px; }
nav div a { text-decoration: none; font-size: 13px; color: var(--muted); } nav div a:hover { color: var(--ink); }

.hero { padding-block: 72px 56px; display: grid; gap: 22px; }
.hero p { font-size: 15px; color: var(--muted); max-width: 62ch; }
.cta { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 6px; }
.btn { font: 500 13px var(--mono); padding: 11px 16px; text-decoration: none; border: 1.5px solid var(--ink); }
.btn.solid { background: var(--ink); color: var(--bg); }

section { padding-block: 56px; border-top: 1px solid var(--line); }
.head { display: grid; gap: 12px; margin-bottom: 28px; }
.head p { color: var(--muted); max-width: 70ch; }

/* the figure */
.fig { border: 1.5px solid var(--rule); background: var(--surface); }
.fig-bar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; padding: 10px 14px; border-bottom: 1.5px solid var(--rule); }
.tabs { display: flex; flex-wrap: wrap; gap: 6px; }
.tabs button { font: 500 11px var(--mono); letter-spacing: 0.08em; text-transform: uppercase; padding: 7px 10px; cursor: pointer;
  background: transparent; color: var(--muted); border: 1px solid var(--line); }
.tabs button[aria-selected="true"] { background: var(--ink); color: var(--bg); border-color: var(--ink); }
.fig-body { padding: 26px 22px 22px; display: grid; gap: 26px; }
.carry { text-align: center; display: grid; gap: 6px; }
.carry .what { font-size: 13px; letter-spacing: 0.06em; text-transform: uppercase; }
.carry .what b { color: var(--accent); margin-right: 8px; }
.f { display: inline-grid; place-items: center; width: 18px; height: 18px; border-radius: 50%; border: 1.5px solid var(--accent);
  color: var(--accent); font: 700 10px var(--mono); vertical-align: -3px; margin-right: 6px; }
.track { display: grid; grid-template-columns: repeat(var(--n), minmax(0, 1fr)); gap: 0 22px; align-items: start; min-height: 200px; }
.cell { display: grid; gap: 0; position: relative; min-width: 0; }
.node { border: 1px solid var(--line); background: var(--bg); padding: 16px 8px 14px; min-height: 138px; display: grid; gap: 6px;
  align-content: start; text-align: center; position: relative; transition: border-color .25s, background .25s; }
.cell:not(:last-child) .node::after { content: "\\2192"; position: absolute; right: -18px; top: 50%; transform: translateY(-50%); color: var(--muted); font-size: 13px; }
.node .num { font-size: 11px; letter-spacing: 0.1em; color: var(--muted); }
.node .name { font: 600 13px/1.2 var(--display); text-transform: uppercase; letter-spacing: 0.04em; overflow-wrap: anywhere; }
.node .note { font-size: 11px; line-height: 1.4; color: var(--muted); }
.node .opt { font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); }
.node.planned { border-style: dashed; }
.node .badge { position: absolute; top: -10px; left: 50%; transform: translateX(-50%); opacity: 0; transition: opacity .2s; background: var(--surface); margin: 0; }
.cell.here .node { border-color: var(--accent); background: var(--accent-soft); }
.cell.here .badge { opacity: 1; }
.cell.past .node { border-color: var(--ok); }
.cell.past .num::after { content: " \\2713"; color: var(--ok); }
.gate { position: relative; z-index: 1; justify-self: end; margin-right: -11px; transform: translateX(50%); display: grid; justify-items: center; gap: 4px; width: max-content; max-width: 150px; text-align: center; }
.gate::before { content: ""; width: 1.5px; height: 18px; background: var(--muted); }
.gate span { font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; }
.gate small { font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); opacity: 0; transition: opacity .2s; }
.cell.held .gate span { color: var(--accent); } .cell.held .gate::before { background: var(--accent); }
.cell.held .gate small { opacity: 1; color: var(--accent); }
.cell:last-child .gate { justify-self: center; margin: 0; transform: none; }
.caption { border: 1px solid var(--line); padding: 12px; text-align: center; font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); }
.caption b { color: var(--ink); font-weight: 500; }

/* rows: numbered notes beside a figure */
.split { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); border: 1.5px solid var(--rule); background: var(--surface); }
.notes { display: grid; }
.note-row { display: grid; grid-template-columns: 34px minmax(0, 1fr); gap: 4px 10px; padding: 22px; border-bottom: 1px solid var(--line); }
.note-row:last-child { border-bottom: 0; }
.note-row .n { font-size: 11px; color: var(--muted); padding-top: 5px; }
.note-row p { grid-column: 2; color: var(--muted); font-size: 13px; }
.side { border-left: 1.5px solid var(--rule); padding: 22px; display: grid; gap: 14px; align-content: center; min-width: 0;
  background: radial-gradient(var(--dot) 1px, transparent 1px) 0 0 / 14px 14px; }
.code { background: var(--code); color: var(--code-ink); font: 12px/1.65 var(--mono); padding: 16px; overflow-x: auto; margin: 0; }
.code .k { color: #ff9a76; } .code .c { color: var(--code-dim); }
.tree { background: var(--surface); border: 1px solid var(--line); padding: 14px 16px; font: 12px/1.8 var(--mono); white-space: pre; overflow-x: auto; margin: 0; }
.sheet { background: var(--surface); border: 1px solid var(--line); font-size: 12px; min-width: 0; }
.sheet-top { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; padding: 10px 12px; border-bottom: 1px solid var(--line); }
.sheet-top b { color: var(--ok); font-weight: 500; }
.sheet-scroll { overflow-x: auto; }
.sheet table { width: 100%; border-collapse: collapse; }
.sheet th, .sheet td { text-align: left; padding: 7px 12px; border-bottom: 1px solid var(--line); white-space: nowrap; }
.sheet th { font-weight: 500; font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); }
.sheet tr:last-child td { border-bottom: 0; } .sheet td:last-child { color: var(--ok); }
.eg { font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); }

.steps { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border: 1.5px solid var(--rule); background: var(--surface); }
.step { padding: 22px; display: grid; gap: 10px; align-content: start; border-right: 1px solid var(--line); min-width: 0; }
.step:last-child { border-right: 0; }
.step p { color: var(--muted); font-size: 13px; }
.cmd { position: relative; min-width: 0; }
.cmd pre { margin: 0; background: var(--code); color: var(--code-ink); padding: 34px 14px 14px; font: 12px/1.65 var(--mono); white-space: pre-wrap; overflow-wrap: anywhere; }
.cmd button { position: absolute; top: 8px; right: 8px; font: 500 10px var(--mono); letter-spacing: 0.08em; text-transform: uppercase;
  background: transparent; color: var(--code-dim); border: 1px solid #3a4348; padding: 4px 7px; cursor: pointer; }
.status { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); border: 1.5px solid var(--rule); background: var(--surface); }
.status div { padding: 22px; display: grid; gap: 10px; align-content: start; }
.status div + div { border-left: 1px solid var(--line); }
.status ul { margin: 0; padding: 0; list-style: none; display: grid; gap: 7px; font-size: 13px; }
.status li::before { content: "\\2713"; color: var(--ok); margin-right: 10px; }
.status .later li::before { content: "\\25CB"; color: var(--muted); }
footer { padding-block: 28px; border-top: 1px solid var(--line); display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px 20px; font-size: 12px; color: var(--muted); }

@media (max-width: 860px) {
  nav div a:not(.keep) { display: none; }
  .hero { padding-block: 48px 40px; }
  .split, .steps, .status { grid-template-columns: minmax(0, 1fr); }
  .side { border-left: 0; border-top: 1.5px solid var(--rule); }
  .step { border-right: 0; border-bottom: 1px solid var(--line); } .step:last-child { border-bottom: 0; }
  .status div + div { border-left: 0; border-top: 1px solid var(--line); }
  .track { grid-template-columns: minmax(0, 1fr); gap: 0; min-height: 0; }
  .node { min-height: 0; grid-template-columns: 34px minmax(0, 1fr); text-align: left; column-gap: 10px; padding: 12px 14px; }
  .node .num { grid-row: span 3; padding-top: 2px; } .node .note, .node .opt { grid-column: 2; }
  .cell:not(:last-child) .node::after { content: none; }
  .cell { padding-bottom: 16px; }
  .cell:not(:last-child)::after { content: "\\2193"; position: absolute; bottom: -3px; left: 26px; color: var(--muted); font-size: 12px; }
  .node .badge { left: auto; right: 10px; top: 12px; transform: none; background: transparent; }
  .gate, .cell:last-child .gate { justify-self: start; margin: 0 0 0 44px; transform: none; max-width: none; justify-items: start; grid-auto-flow: column; align-items: center; gap: 8px; padding-top: 8px; }
  .gate::before { width: 14px; height: 1.5px; }
}
@media (prefers-reduced-motion: reduce) { .node, .gate small, .node .badge { transition: none; } }
"""

FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700'
         '&family=Schibsted+Grotesk:wght@500;600&display=swap">')

SCRIPT = """
<script>
(function () {
  var lines = %s;
  var track = document.getElementById('track'), carry = document.getElementById('carry');
  var tabs = document.querySelectorAll('.tabs button'), timer = null;
  var still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  function esc(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
  function draw(line) {
    track.style.setProperty('--n', line.nodes.length);
    track.innerHTML = line.nodes.map(function (n, i) {
      return '<div class="cell"><div class="node' + (n.planned ? ' planned' : '') + '"><span class="f badge">F</span>' +
        '<span class="num">0' + (i + 1) + '</span><span class="name">' + esc(n.name) + '</span>' +
        '<span class="note">' + esc(n.note) + '</span>' +
        (n.optional ? '<span class="opt">optional</span>' : '') + (n.planned ? '<span class="opt">planned</span>' : '') + '</div>' +
        (n.gate ? '<div class="gate"><span>[' + esc(n.gate) + ']</span><small>waiting for you</small></div>' : '') + '</div>';
    }).join('');
    carry.innerHTML = '<div class="what"><span class="f">F</span><b>' + esc(line.source) + '</b>' + esc(line.ref) + ' &middot; ' + esc(line.title) + '</div>' +
      '<div class="eg">example issue &middot; the foreman carries it down the line</div>';
  }
  function play(line) {
    clearInterval(timer);
    var cells = track.children, i = 1, hold = 0;
    function show() {
      for (var k = 0; k < cells.length; k++) {
        cells[k].classList.toggle('past', k < i);
        cells[k].classList.toggle('here', k === i);
        cells[k].classList.toggle('held', k === i && hold > 0);
      }
    }
    hold = line.nodes[i].gate ? 1 : 0;
    show();
    if (still) { return; }
    timer = setInterval(function () {
      if (line.nodes[i].gate && hold < 2) { hold++; show(); return; }
      hold = 0; i = (i + 1) %% cells.length; show();
    }, 1300);
  }
  function pick(id) {
    var line = lines.filter(function (l) { return l.id === id; })[0];
    tabs.forEach(function (t) { t.setAttribute('aria-selected', t.dataset.id === id ? 'true' : 'false'); });
    draw(line); play(line);
  }
  tabs.forEach(function (t) { t.addEventListener('click', function () { pick(t.dataset.id); }); });
  pick(lines[0].id);
  document.querySelectorAll('.cmd button').forEach(function (button) {
    button.addEventListener('click', function () {
      var pre = button.parentNode.querySelector('pre');
      var done = function () { button.textContent = 'copied'; setTimeout(function () { button.textContent = 'copy'; }, 1400); };
      var select = function () { var r = document.createRange(); r.selectNodeContents(pre); var s = getSelection(); s.removeAllRanges(); s.addRange(r); };
      try { navigator.clipboard.writeText(pre.textContent).then(done, select); } catch (e) { select(); }
    });
  });
})();
</script>
"""


def static_track(line_data):
    """The first line, drawn without script so the page is complete before it runs."""
    cells = []
    for i, node in enumerate(line_data["nodes"]):
        extra = ('<span class="opt">optional</span>' if node.get("optional") else "") + \
                ('<span class="opt">planned</span>' if node.get("planned") else "")
        gate = '<div class="gate"><span>[{}]</span><small>waiting for you</small></div>'.format(node["gate"]) if node.get("gate") else ""
        cells.append('<div class="cell"><div class="node{}"><span class="f badge">F</span><span class="num">0{}</span>'
                     '<span class="name">{}</span><span class="note">{}</span>{}</div>{}</div>'.format(
                         " planned" if node.get("planned") else "", i + 1, node["name"], node["note"], extra, gate))
    return "".join(cells)


def cmd(text):
    return '<div class="cmd"><pre>{}</pre><button type="button">copy</button></div>'.format(html.escape(text))


def body(lines):
    first = lines[0]
    tabs = "".join('<button type="button" role="tab" data-id="{}" aria-selected="{}">{}</button>'.format(
        l["id"], "true" if l is first else "false", l["tab"]) for l in lines)
    return """
<div class="wrap">
<nav><a class="brand" href="#top"><span>F</span>Software Factory</a>
  <div><a href="#flow">flow</a><a href="#config">config</a><a href="#start">get started</a><a class="keep" href="%(repo)s">github</a></div></nav>

<header class="hero" id="top">
  <span class="tag"><b># software factory</b> <i>[runs on claude code]</i></span>
  <h1>Your development process, run as a line.</h1>
  <p>define the line once. agents work each stage. it stops only where you decide.</p>
  <div class="cta"><a class="btn solid" href="#start">get started</a><a class="btn" href="%(repo)s">view on github</a></div>
</header>

<section id="flow">
  <div class="head"><span class="tag"><b># issue flow</b></span><h2>How work moves through a factory</h2>
    <p>An issue lands from the tracker your team already uses. The foreman carries it down the line, and the line stops wherever you put a review.</p></div>
  <div class="fig">
    <div class="fig-bar"><span class="tag">[ fig. 1 · the line ]</span><div class="tabs" role="tablist" aria-label="Sample factory">%(tabs)s</div></div>
    <div class="fig-body">
      <div class="carry" id="carry"><div class="what"><span class="f">F</span><b>%(source)s</b>%(ref)s &middot; %(title)s</div>
        <div class="eg">example issue &middot; the foreman carries it down the line</div></div>
      <div class="track" id="track" style="--n:%(n)s">%(track)s</div>
      <div class="caption"><b>the foreman moves the work</b> &middot; it stops only where you decide &middot; <b>merge is always yours</b></div>
    </div>
  </div>
</section>

<section id="config">
  <div class="head"><span class="tag"><b># configuration</b></span><h2>Your line, defined in code</h2></div>
  <div class="split">
    <div class="notes">
      <div class="note-row"><span class="n">01</span><h3>One file per repository</h3><p>The stages, in order, and where a person reviews. Versioned in git, reviewed like code.</p></div>
      <div class="note-row"><span class="n">02</span><h3>A skill for every stage</h3><p>Each stage follows a short skill written for that one job. Swap in your own.</p></div>
      <div class="note-row"><span class="n">03</span><h3>Start from where work lives</h3><p>GitHub, GitLab, Jira, or a file. Changing source is three lines.</p></div>
      <div class="note-row"><span class="n">04</span><h3>Move the reviews</h3><p>Add a review before a stage you want to see. Remove one to let work flow.</p></div>
    </div>
    <div class="side">
      <pre class="code"><span class="c"># targets/shop/factory.json</span>
<span class="k">"source"</span>: { "type": "github", "repo": "acme/shop" },
<span class="k">"stages"</span>: [
  { "id": "requirements", "skill": "write-requirements" },
  { "id": "approve-requirements", "by": "human" },
  { "id": "design", "skill": "write-design", "optional": true },
  { "id": "tasks", "skill": "write-tasks" },
  { "id": "build", "skill": "build-tasks" },
  { "id": "verify", "skill": "verify" }
]</pre>
      <pre class="tree">targets/shop/
├── factory.json     the line
├── AGENTS.md        your engineering rules
├── presubmit        your build and tests
└── skills/          one folder per stage</pre>
    </div>
  </div>
</section>

<section>
  <div class="head"><span class="tag"><b># trust</b></span><h2>Done means proven</h2></div>
  <div class="split">
    <div class="notes">
      <div class="note-row"><span class="n">01</span><h3>Maker and checker</h3><p>One agent builds a task. A different one, with fresh eyes, checks it.</p></div>
      <div class="note-row"><span class="n">02</span><h3>Evidence for every gate</h3><p>Each check records what was expected and what was found.</p></div>
      <div class="note-row"><span class="n">03</span><h3>Nothing ticked on trust</h3><p>Work without evidence goes back down the line on its own.</p></div>
      <div class="note-row"><span class="n">04</span><h3>You read a sheet, not a log</h3><p>One page per gate, readable in a minute.</p></div>
    </div>
    <div class="side">
      <div class="sheet">
        <div class="sheet-top"><span>evidence/2-backend-gate.md</span><b>status: pass · 5/5</b></div>
        <div class="sheet-scroll"><table>
          <tr><th>check</th><th>expected</th><th>actual</th><th></th></tr>
          <tr><td>build errors</td><td>0</td><td>0</td><td>&#10003;</td></tr>
          <tr><td>POST /api/orders/export</td><td>201</td><td>201</td><td>&#10003;</td></tr>
          <tr><td>export without permission</td><td>403</td><td>403</td><td>&#10003;</td></tr>
          <tr><td>raw sql in controller</td><td>0</td><td>0</td><td>&#10003;</td></tr>
          <tr><td>integration tests</td><td>12 passed</td><td>12 passed</td><td>&#10003;</td></tr>
        </table></div>
      </div>
      <span class="eg">example sheet, for illustration</span>
    </div>
  </div>
</section>

<section id="start">
  <div class="head"><span class="tag"><b># get started</b></span><h2>Three commands to a running line</h2></div>
  <div class="steps">
    <div class="step"><span class="tag dim">01</span><h3>Start from a sample</h3><p>Pick the closest of the four and point it at your repository.</p>%(c1)s</div>
    <div class="step"><span class="tag dim">02</span><h3>Make it yours</h3><p>Set the source, your rules and your tests. Move the reviews.</p>%(c2)s</div>
    <div class="step"><span class="tag dim">03</span><h3>Run one issue</h3><p>It stops at your first review.</p>%(c3)s</div>
  </div>
</section>

<section>
  <div class="head"><span class="tag"><b># status</b></span><h2>What works today</h2></div>
  <div class="status">
    <div><span class="tag">working</span><ul><li>four sample factories</li><li>read from github, gitlab, or a file</li><li>review stops, approve to continue</li>
      <li>evidence checks send work back</li><li>runs from claude code or headless</li></ul></div>
    <div class="later"><span class="tag dim">planned</span><ul><li>open the merge request</li><li>comment and label on the issue</li><li>approve by label</li>
      <li>scheduled, unattended runs</li><li>jira, tested against a real instance</li><li>visual editor for the line</li></ul></div>
  </div>
</section>

<footer><span>software factory · runs on claude code</span><a href="%(repo)s">%(repo_short)s</a></footer>
</div>
""" % {
        "repo": REPO_URL, "repo_short": REPO_URL.replace("https://", ""), "tabs": tabs,
        "source": first["source"], "ref": first["ref"], "title": first["title"],
        "n": len(first["nodes"]), "track": static_track(first),
        "c1": cmd("python3 factory/flow.py init shop \\\n  --sample backend-api \\\n  --repo ~/code/shop"),
        "c2": cmd("python3 factory/flow.py --target shop show\npython3 factory/flow.py --target shop validate"),
        "c3": cmd("python3 factory/flow.py --target shop \\\n  start --issue 42\npython3 factory/flow.py --target shop run"),
    }


def main():
    lines = [line(name) for name in ORDER]
    head = "<title>Software Factory</title>{}<style>{}</style>".format(FONTS, STYLE)
    content = body(lines) + SCRIPT % json.dumps(lines)
    docs = HOME / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">{}</head><body>{}</body></html>\n'.format(
            head, content))
    print(docs / "index.html")


if __name__ == "__main__":
    main()
