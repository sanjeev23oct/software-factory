"""Renders the factory board as one static HTML page.

`factory.py board` writes it to site/. The page has no script and no server,
so any static host can serve it.
"""

import datetime
import html
import json
import re

STEPS = ("Triage", "Spec", "Implement", "Review", "Merge")

STYLE = """
/* Layout: a summary strip, then one row per issue with a five-step track; each row opens to its history. */
:root {
  --bg: #edf0f3; --surface: #f8fafb; --ink: #17212b; --muted: #5a6875; --line: #cfd6dd;
  --accent: #0b6a86; --agent: #0b6a86; --human: #9a5b00; --blocked: #b3261e; --done: #2b7a4b;
  --display: "Archivo", "Helvetica Neue", Arial, sans-serif;
  --body: "IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #11181f; --surface: #18222b; --ink: #e3e9ee; --muted: #94a3b0; --line: #2c3945;
    --accent: #5bb8d4; --agent: #5bb8d4; --human: #e0a84a; --blocked: #f08a82; --done: #6fc391;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #11181f; --surface: #18222b; --ink: #e3e9ee; --muted: #94a3b0; --line: #2c3945;
  --accent: #5bb8d4; --agent: #5bb8d4; --human: #e0a84a; --blocked: #f08a82; --done: #6fc391;
  color-scheme: dark;
}
body { background: var(--bg); color: var(--ink); font: 15px/1.5 var(--body); }
.page { max-width: 1040px; margin: 0 auto; padding-inline: 20px; padding-block: 36px 64px; display: grid; gap: 28px; }
header { display: grid; gap: 6px; }
h1 { font: 800 30px/1.1 var(--display); letter-spacing: -0.01em; margin: 0; text-wrap: balance; }
.sub { color: var(--muted); max-width: 65ch; margin: 0; }
.eyebrow, .tally dt, .who, .step { font: 600 11px/1.2 var(--mono); letter-spacing: 0.08em; text-transform: uppercase; }
.eyebrow { color: var(--muted); }
.tally { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 0; margin: 0;
  border-block: 2px solid var(--ink); }
.tally div { padding: 12px 14px 12px 0; }
.tally dt { color: var(--muted); }
.tally dd { margin: 4px 0 0; font: 800 28px/1 var(--display); font-variant-numeric: tabular-nums; }
.issues { display: grid; gap: 10px; }
details { background: var(--surface); border: 1px solid var(--line); border-radius: 4px; }
summary { list-style: none; cursor: pointer; padding: 14px 16px; display: grid; gap: 12px 18px;
  grid-template-columns: minmax(0, 1fr) auto; align-items: center; }
summary::-webkit-details-marker { display: none; }
summary:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.head { min-width: 0; display: grid; gap: 4px; }
.title { font: 700 17px/1.25 var(--display); overflow-wrap: anywhere; }
.id { font: 500 13px var(--mono); color: var(--muted); margin-right: 8px; }
.meta { color: var(--muted); font-size: 13px; overflow-wrap: anywhere; }
.who { padding: 5px 9px; border: 1.5px solid currentColor; border-radius: 2px; white-space: nowrap; justify-self: end; }
.who.agent { color: var(--agent); } .who.human { color: var(--human); }
.who.blocked { color: var(--blocked); } .who.done { color: var(--done); }
.track { grid-column: 1 / -1; display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 4px; margin: 0; padding: 0; list-style: none; }
.step { color: var(--muted); padding-top: 7px; border-top: 4px solid var(--line); overflow: hidden; text-overflow: ellipsis; }
.step.done { border-color: var(--done); color: var(--ink); }
.step.current { border-color: var(--accent); color: var(--accent); }
.step.current.human { border-color: var(--human); color: var(--human); }
.step.current.blocked { border-color: var(--blocked); color: var(--blocked); }
.step.skipped { border-top-style: dashed; text-decoration: line-through; }
.history { border-top: 1px solid var(--line); padding: 4px 16px 16px; display: grid; gap: 0; }
.entry { padding: 14px 0; border-bottom: 1px solid var(--line); display: grid; gap: 6px; min-width: 0; }
.entry:last-child { border-bottom: 0; padding-bottom: 0; }
.entry b { font: 600 12px var(--mono); }
.entry time { font: 12px var(--mono); color: var(--muted); margin-left: 8px; }
.entry pre { margin: 0; font: 13px/1.55 var(--body); white-space: pre-wrap; overflow-wrap: anywhere; max-width: 78ch; }
.labels { display: flex; flex-wrap: wrap; gap: 5px; }
.labels span { font: 11px var(--mono); color: var(--muted); border: 1px solid var(--line); border-radius: 2px; padding: 1px 6px; }
footer { color: var(--muted); font-size: 13px; }
@media (max-width: 520px) { h1 { font-size: 24px; } .step { font-size: 9px; letter-spacing: 0.02em; } }
"""

FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@700;800'
         '&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;600&display=swap">')


def step_index(issue):
    """How far along the track the issue is. 5 means merged."""
    if issue.has("merged"):
        return 5
    for index, labels in ((4, ("agent-approved",)), (3, ("in-review",)),
                          (2, ("changes-requested", "ready-to-implement")),
                          (1, ("ready-to-spec", "spec-in-review", "spec-reviewed", "spec-changes-requested"))):
        if issue.has(*labels):
            return index
    if issue.has("needs-triage") or not issue.has("triaged"):
        return 0
    return 2 if issue.has("agent:bug") else 1


def history(issue):
    opening, *comments = re.split(r"\n\n---\n\*\*(.+?)\*\* · (.+?)\n\n", issue.body)
    entries = [(issue.meta.get("author", "reporter"), "filed", opening.strip())]
    entries += [(comments[i], comments[i + 1], comments[i + 2].strip()) for i in range(0, len(comments), 3)]
    return entries


def render_issue(issue, actor, what, cost):
    e = html.escape
    kind = "done" if actor == "-" else "blocked" if what.startswith("blocked") else "agent" if actor == "agent" else "human"
    who = {"done": "Merged", "blocked": "Blocked", "agent": "Agent next", "human": "Maintainer next"}[kind]
    index, steps = step_index(issue), []
    for i, name in enumerate(STEPS):
        state = "done" if i < index else "current " + kind if i == index else ""
        if name == "Spec" and issue.has("agent:bug"):
            state = "skipped"
        steps.append('<li class="step {}">{}</li>'.format(state, name))
    entries = "".join('<div class="entry"><div><b>{}</b><time>{}</time></div><pre>{}</pre></div>'.format(
        e(w), e(t), e(text)) for w, t, text in history(issue))
    labels = "".join("<span>{}</span>".format(e(l)) for l in issue.labels)
    spend = " · ${:.2f} agent spend".format(cost) if cost else ""
    return ('<details><summary><div class="head"><div class="title"><span class="id">{id}</span>{title}</div>'
            '<div class="meta">{what}{spend}</div></div><span class="who {kind}">{who}</span>'
            '<ol class="track">{steps}</ol></summary>'
            '<div class="history"><div class="entry"><div class="labels">{labels}</div></div>{entries}</div></details>'
            ).format(id=e(issue.id), title=e(issue.title), what=e(what.replace("`", "")), spend=spend, kind=kind,
                     who=who, steps="".join(steps), labels=labels, entries=entries)


def render(rows, name, fragment=False):
    """rows: (issue, actor, what, cost) per issue."""
    count = lambda test: sum(1 for r in rows if test(r))
    tally = [
        ("With agents", count(lambda r: r[1] == "agent")),
        ("With a maintainer", count(lambda r: r[1] == "human" and not r[2].startswith("blocked"))),
        ("Blocked", count(lambda r: r[2].startswith("blocked"))),
        ("Merged", count(lambda r: r[1] == "-")),
        ("Agent spend", "${:.2f}".format(sum(r[3] for r in rows))),
    ]
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body = (
        '<div class="page"><header><div class="eyebrow">Software factory · {}</div>'
        "<h1>Factory board</h1>"
        '<p class="sub">Agents triage, spec, implement and review each issue. A maintainer decides what is '
        "ready and what merges. Open an issue to read its full history.</p></header>"
        '<dl class="tally">{}</dl><section class="issues">{}</section>'
        "<footer>Snapshot taken {}. Agent spend counts headless runs only.</footer></div>"
    ).format(html.escape(name), "".join("<div><dt>{}</dt><dd>{}</dd></div>".format(k, v) for k, v in tally),
             "".join(render_issue(*r) for r in rows), stamp)
    head = "<title>Factory Board</title>{}<style>{}</style>".format(FONTS, STYLE)
    if fragment:
        return head + body
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">{}</head><body style="margin:0">{}'
            "</body></html>").format(head, body)


def costs(runs_dir):
    return sum(json.loads(p.read_text()).get("cost_usd") or 0 for p in runs_dir.glob("*-*.json"))
