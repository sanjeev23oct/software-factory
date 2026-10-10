#!/usr/bin/env python3
"""Render docs/index.html, the page that explains the factory concept.

The stage strips are drawn from factories/*/factory.json, so the page cannot
drift from the sample factories. Run it after changing a sample:

    python3 factory/scripts/build_docs.py
"""

import html
import json
from pathlib import Path

HOME = Path(__file__).resolve().parent.parent.parent
ORDER = ["spec-driven", "backend-api", "ui-app", "bugfix"]
STARTS = {"file": "a file", "github": "GitHub issues", "gitlab": "GitLab issues", "jira": "Jira issues"}

STYLE = """
/* Layout: one reading column; stage strips are the recurring figure and may run wider than the text. */
:root {
  --bg: #edf0f3; --surface: #f8fafb; --ink: #17212b; --muted: #5a6875; --line: #cfd6dd;
  --accent: #0b6a86; --script: #4b5a68; --agent: #0b6a86; --human: #9a5b00; --human-bg: #f6e7c8; --code-bg: #e2e7ec;
  --display: "Archivo", "Helvetica Neue", Arial, sans-serif;
  --body: "IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #11181f; --surface: #18222b; --ink: #e3e9ee; --muted: #94a3b0; --line: #2c3945;
    --accent: #5bb8d4; --script: #a9b6c2; --agent: #5bb8d4; --human: #e0a84a; --human-bg: #3a2c10; --code-bg: #1f2b35;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #11181f; --surface: #18222b; --ink: #e3e9ee; --muted: #94a3b0; --line: #2c3945;
  --accent: #5bb8d4; --script: #a9b6c2; --agent: #5bb8d4; --human: #e0a84a; --human-bg: #3a2c10; --code-bg: #1f2b35;
  color-scheme: dark;
}
body { background: var(--bg); color: var(--ink); font: 16px/1.6 var(--body); margin: 0; }
.page { max-width: 880px; margin: 0 auto; padding-inline: 20px; padding-block: 48px 80px; display: grid; gap: 56px; }
section, header { display: grid; gap: 16px; min-width: 0; }
h1 { font: 800 clamp(30px, 6vw, 46px)/1.08 var(--display); letter-spacing: -0.015em; margin: 0; text-wrap: balance; max-width: 18ch; }
h2 { font: 800 24px/1.2 var(--display); margin: 0; text-wrap: balance; padding-top: 14px; border-top: 2px solid var(--ink); }
h3 { font: 700 17px/1.3 var(--display); margin: 0; }
p, ul, ol { margin: 0; max-width: 66ch; }
ul, ol { padding-left: 1.2em; display: grid; gap: 6px; }
.lede { font-size: 19px; line-height: 1.5; max-width: 60ch; }
.eyebrow, .chip, .legend span, th { font: 600 11px/1.2 var(--mono); letter-spacing: 0.07em; text-transform: uppercase; }
.eyebrow { color: var(--muted); }
a { color: var(--accent); }
a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
code { font: 0.88em var(--mono); background: var(--code-bg); padding: 1px 5px; border-radius: 3px; overflow-wrap: anywhere; }
pre { margin: 0; background: var(--code-bg); border-radius: 4px; padding: 14px 16px; overflow-x: auto; font: 13px/1.55 var(--mono); }
pre code { background: none; padding: 0; font-size: inherit; overflow-wrap: normal; }
.kinds { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; }
.kind { display: grid; gap: 6px; align-content: start; padding-top: 10px; border-top: 4px solid var(--c); min-width: 0; }
.kind h3 { color: var(--c); }
.kind p { font-size: 15px; }
.script { --c: var(--script); } .agent { --c: var(--agent); } .human { --c: var(--human); }
.factory { display: grid; gap: 10px; padding-block: 18px; border-bottom: 1px solid var(--line); min-width: 0; }
.factory:last-of-type { border-bottom: 0; }
.factory .meta { color: var(--muted); font-size: 14px; }
.strip { display: flex; flex-wrap: wrap; gap: 6px 4px; align-items: center; list-style: none; padding: 0; max-width: none; }
.strip li { display: flex; align-items: center; gap: 4px; }
.strip li + li::before { content: "\\2192"; color: var(--muted); font: 13px var(--mono); }
.chip { padding: 6px 8px; border: 1.5px solid var(--c); color: var(--c); border-radius: 2px; white-space: nowrap; text-transform: none; letter-spacing: 0; font-size: 12px; }
.chip.human { background: var(--human-bg); font-weight: 600; }
.chip.optional { border-style: dashed; }
.chip.off { opacity: 0.55; border-style: dotted; }
.legend { display: flex; flex-wrap: wrap; gap: 8px 18px; color: var(--muted); }
.legend span { display: flex; align-items: center; gap: 6px; }
.legend i { width: 14px; height: 14px; border: 1.5px solid var(--c); border-radius: 2px; display: block; }
.legend i.human { background: var(--human-bg); } .legend i.optional { border-style: dashed; --c: var(--muted); }
.scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 15px; }
th { text-align: left; color: var(--muted); padding: 0 14px 8px 0; border-bottom: 1px solid var(--ink); white-space: nowrap; }
td { padding: 10px 14px 10px 0; border-bottom: 1px solid var(--line); vertical-align: top; }
td:first-child { font-weight: 600; white-space: nowrap; }
.steps { counter-reset: step; list-style: none; padding: 0; gap: 22px; max-width: none; }
.steps > li { counter-increment: step; display: grid; grid-template-columns: 34px minmax(0, 1fr); gap: 4px 12px; }
.steps > li::before { content: counter(step); font: 800 22px/1.2 var(--display); color: var(--accent); grid-row: span 3; }
.steps > li > * { grid-column: 2; }
footer { color: var(--muted); font-size: 14px; }
"""

FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@700;800'
         '&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;600&display=swap">')


def strip(stages):
    items = []
    for stage in stages:
        classes = ["chip", stage["by"]]
        classes += ["optional"] if stage.get("optional") and stage.get("enabled", True) else []
        classes += ["off"] if not stage.get("enabled", True) else []
        items.append('<li><span class="{}">{}</span></li>'.format(" ".join(classes), html.escape(stage["id"])))
    return '<ol class="strip">{}</ol>'.format("".join(items))


def factories():
    blocks = []
    for name in ORDER:
        d = json.loads((HOME / "factories" / name / "factory.json").read_text())
        live = [s for s in d["stages"] if s.get("enabled", True)]
        humans = sum(1 for s in live if s["by"] == "human")
        scripts = sum(1 for s in live if s["by"] == "script")
        blocks.append(
            '<div class="factory"><h3>{}</h3><p>{}</p>{}'
            '<div class="meta">Starts from {} · {} human decision{} · {} of {} stages are scripts</div></div>'.format(
                html.escape(name), html.escape(d["description"]), strip(d["stages"]),
                STARTS[d["source"]["type"]], humans, "" if humans == 1 else "s", scripts, len(live)))
    return "".join(blocks)


def body():
    sample = json.loads((HOME / "factories" / "spec-driven" / "factory.json").read_text())
    excerpt = {"source": {"type": "github", "repo": "acme/shop", "label": "factory"}, "spec_dir": sample["spec_dir"],
               "limits": sample["limits"],
               "stages": [{k: v for k, v in s.items() if k in ("id", "by", "skill", "optional", "on_fail")}
                          for s in sample["stages"][:6]] + ["..."]}
    excerpt_text = json.dumps(excerpt, indent=2)
    # One stage per line reads better than one key per line.
    for stage in excerpt["stages"][:-1]:
        excerpt_text = excerpt_text.replace(json.dumps(stage, indent=2).replace("\n", "\n    "), json.dumps(stage))
    return """
<div class="page">
<header>
  <div class="eyebrow">Software factory · concept and samples</div>
  <h1>Decide once who does each step</h1>
  <p class="lede">A software factory is a written definition of how a piece of work travels from a request to
  a reviewed change. For every step it answers one question: is this done by a script, by an AI agent, or by a person?</p>
  <p>Once that is written down, the factory can run it for you. Scripts and agents do their steps unattended.
  The factory stops only where you said a person is needed, and waits.</p>
</header>

<section>
  <h2>Three kinds of step</h2>
  <div class="kinds">
    <div class="kind script"><h3>Script</h3><p>Anything with one right answer. Fetch the issue, check that every
    task names a skill, run the tests, re-check the evidence. No AI is involved, so it costs nothing and gives the same result every time.</p></div>
    <div class="kind agent"><h3>Agent</h3><p>Anything that needs judgment. Write the requirements, design the change,
    build a task, review a diff. An agent follows a skill, a short document that says how to do that one job.</p></div>
    <div class="kind human"><h3>Human</h3><p>Anything that is a decision about your product. Is this what we want
    to build? Does this screen look right? Should this merge? The factory waits here for as long as it takes.</p></div>
  </div>
  <p>Designing a factory is mostly deciding where the human steps go. Too many and nothing moves without you.
  Too few and you find out about a wrong turn after the work is done.</p>
</section>

<section>
  <h2>Four sample factories</h2>
  <p>Each is a real definition in the repository. They differ in where work comes from, which steps exist, and where a person is asked.</p>
  <div class="legend">
    <span class="script"><i></i>Script</span><span class="agent"><i></i>Agent</span>
    <span class="human"><i class="human"></i>Human</span><span><i class="optional"></i>Optional step</span>
  </div>
  <div>%(factories)s</div>
</section>

<section>
  <h2>What a definition contains</h2>
  <p>A factory is one file, <code>factory.json</code>, plus a folder of skills. This is the start of the
  <code>spec-driven</code> sample, pointed at a GitHub repository:</p>
  <pre><code>%(excerpt)s</code></pre>
  <div class="scroll"><table>
    <tr><th>Part</th><th>What it decides</th></tr>
    <tr><td>source</td><td>Where work comes from, and which label marks an issue as ready for the factory.</td></tr>
    <tr><td>stages</td><td>The steps, in order. Each has an <code>id</code>, who does it (<code>by</code>), and the skill it follows.</td></tr>
    <tr><td>optional</td><td>A step a person may skip when approving, such as a design for a small change.</td></tr>
    <tr><td>on_fail</td><td>Where work goes back to when a script rejects it. The earlier stage redoes it with the findings.</td></tr>
    <tr><td>writes</td><td>The only files an agent step may change. Anything else it touches is rejected.</td></tr>
    <tr><td>limits</td><td>How many attempts a step gets before the item is parked for a person.</td></tr>
  </table></div>
</section>

<section>
  <h2>Where work can start</h2>
  <div class="scroll"><table>
    <tr><th>Source</th><th>How the factory reads it</th><th>State</th></tr>
    <tr><td>GitHub issues</td><td>The <code>gh</code> login on your machine</td><td>Reading and polling tested</td></tr>
    <tr><td>GitLab issues</td><td>The <code>glab</code> login; self-hosted instances work</td><td>Reading and polling tested</td></tr>
    <tr><td>Jira issues</td><td><code>JIRA_BASE_URL</code>, <code>JIRA_EMAIL</code>, <code>JIRA_API_TOKEN</code></td><td>Written, not yet tested against a real Jira</td></tr>
    <tr><td>A file</td><td>Any text or markdown file you point it at</td><td>Tested</td></tr>
  </table></div>
  <p>Every source ends up as the same file, <code>issue_context.md</code>, so the rest of a factory does not care
  where the work came from. To move a factory from Jira to GitHub you change three lines of <code>source</code>.</p>
  <p>The factory only reads from these today. It does not comment, label, or open pull requests.</p>
</section>

<section>
  <h2>Create your own</h2>
  <ol class="steps">
    <li><h3>Start from the nearest sample</h3>
      <p>Pick the one closest to how your team already works, and point it at your repository.</p>
      <pre><code>python3 factory/flow.py init shop --sample backend-api --repo ~/code/shop</code></pre></li>
    <li><h3>Tell it about your repository</h3>
      <p>Three files in <code>targets/shop/</code>: the source in <code>factory.json</code>, your engineering rules in
      <code>AGENTS.md</code>, and your build and test commands in <code>presubmit</code>.</p></li>
    <li><h3>Move the human steps to where you want them</h3>
      <p>Edit the <code>stages</code> list. Delete an approval to let work flow through. Add one before a step you want to see first.
      Mark a step <code>optional</code>. Add a script step for any check you can express as a command.</p>
      <pre><code>python3 factory/flow.py --target shop show
python3 factory/flow.py --target shop validate</code></pre></li>
    <li><h3>Run one real item</h3>
      <p>Take a single issue through before trusting it with more. It stops at your first human step.</p>
      <pre><code>python3 factory/flow.py --target shop start --issue 42
python3 factory/flow.py --target shop run
python3 factory/flow.py --target shop approve GH42</code></pre></li>
  </ol>
</section>

<section>
  <h2>Matching a factory to the work</h2>
  <div class="scroll"><table>
    <tr><th>Kind of work</th><th>What matters</th><th>What the factory does about it</th></tr>
    <tr><td>Backend and data</td><td>API shapes and schema changes are expensive to undo.</td><td>Design is required and has its own approval before any code.</td></tr>
    <tr><td>UI</td><td>A screen can pass every check and still look wrong.</td><td>A visual spec pins text and states; a person looks at the result at the end.</td></tr>
    <tr><td>Bug fixes</td><td>Speed, and proof the bug is really gone.</td><td>No spec. A failing test first, then the fix, then one approval.</td></tr>
    <tr><td>Full-stack features</td><td>Agreement on what is being built.</td><td>One approval on the requirements; scripts police everything after.</td></tr>
  </table></div>
</section>

<section>
  <h2>What keeps it honest</h2>
  <p>An agent saying a task is done proves nothing. These rules hold whatever the definition says. All but the first are enforced by scripts.</p>
  <ul>
    <li><strong>Maker and checker are different agents.</strong> The one that builds a task never runs its gate or writes its evidence. This is an instruction in the build skill, backed by the evidence check below.</li>
    <li><strong>A ticked box needs evidence.</strong> A script confirms the evidence file exists and records a pass, and re-runs the checks it can.</li>
    <li><strong>Every task names a skill.</strong> A script rejects a task list where one does not.</li>
    <li><strong>Agents write only where the step allows.</strong> The factory inspects the files that changed, not what the agent reports.</li>
    <li><strong>Every definition has a human step.</strong> One with none is refused.</li>
    <li><strong>Agents never commit, push, or merge.</strong> The factory commits after its checks pass, on a branch of its own.</li>
  </ul>
</section>

<section>
  <h2>Not built yet</h2>
  <ul>
    <li>Writing back: comments, labels, and opening the merge or pull request.</li>
    <li>Approving by setting a label on the issue. Approval is a command today.</li>
    <li>A scheduler for unattended runs. <code>poll</code> exists; nothing calls it on a timer.</li>
    <li>A screen for editing a definition. It is a JSON file for now.</li>
    <li>Triage as a stage in these definitions. It exists in the older label-driven flow in the same repository.</li>
  </ul>
</section>

<footer>Source: <a href="https://github.com/sanjeev23oct/software-factory">github.com/sanjeev23oct/software-factory</a>.
The stage strips on this page are generated from the sample definitions. The approach follows the factory Warp runs on its own repository.</footer>
</div>
""" % {"factories": factories(), "excerpt": html.escape(excerpt_text)}


def main():
    head = "<title>Software Factory Guide</title>{}<style>{}</style>".format(FONTS, STYLE)
    content = body()
    docs = HOME / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">{}</head><body>{}</body></html>\n'.format(
            head, content))
    # The same page without the document shell, for hosts that add their own.
    site = HOME / "site"
    site.mkdir(exist_ok=True)
    (site / "guide.fragment.html").write_text(head + content)
    print(docs / "index.html")


if __name__ == "__main__":
    main()
