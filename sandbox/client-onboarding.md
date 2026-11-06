# {{CLIENT}}: getting started with the software factory

You already build with Claude Code on your laptop: you describe a change in
the terminal, Claude edits the files, you check the result and push it. The
software factory does the same kind of work with Claude agents, but on our
server, in fixed steps, with a second agent checking every piece. You take
part at two points: you approve what will be built, and you approve what was
built.

## See a finished example first

Start by looking at a real request from start to finish. Everything described
below happened here. Someone asked for a CRM dashboard in plain words,
approved twice, and 17 minutes later it was built, checked and waiting for
review.

**The result, live.** This uses the sample's login, which we send you
separately.

| What | Link |
|---|---|
| Where the request stands: every step ticked | {{SAMPLE_SITE}}/status/ |
| **Try it**: the CRM dashboard that was built | {{SAMPLE_SITE}}/GL1/ |
| The app before the request: an empty page | {{SAMPLE_SITE}}/main/ |

**The conversation and the paperwork, in GitLab.** This uses your own GitLab
login; we give you read-only access to the sample project.

| What | Link |
|---|---|
| The request, with every comment and both approvals | {{GITLAB}}/{{SAMPLE_PROJECT}}/-/issues/1 |
| What the factory understood | {{GITLAB}}/{{SAMPLE_PROJECT}}/-/blob/factory/GL1/{{SAMPLE_SPEC}}/requirements.md |
| The plan, split into sections | {{GITLAB}}/{{SAMPLE_PROJECT}}/-/blob/factory/GL1/{{SAMPLE_SPEC}}/tasks.md |
| A checker's evidence for one section | {{GITLAB}}/{{SAMPLE_PROJECT}}/-/blob/factory/GL1/{{SAMPLE_SPEC}}/evidence/1-logic-gate.md |
| The finished work, ready for review | {{GITLAB}}/{{SAMPLE_PROJECT}}/-/merge_requests/1 |

The sample is for looking only. Please file your own requests in your own
project, not there.

## What changes for you

| | Claude Code on your laptop | Factory: where | Factory: how |
|---|---|---|---|
| **Ask** | A prompt in your terminal | A new **issue** in your GitLab project | Fill in the Feature form: what should change, and how you'll know it works. Press **Create issue**. |
| **Agree what to build** | You and Claude settle it in the chat as you go | `requirements.md`, on the branch `factory/GL<n>`. A comment on your issue links to it. | Click the link in the comment and read it in GitLab. Then reply on the issue: `approve`, or what to change. |
| **Plan the work** | Claude proposes steps in the chat | `tasks.md`, next to the requirements | Written by an agent after your first `approve`. You don't need to act; read it if you're curious. |
| **Build** | Claude edits files on your laptop, which has to stay on | Our server, on the branch `factory/GL<n>` | Nothing to do. A **Factory progress** comment on your issue lists each step as it happens. You can close your laptop. |
| **Check** | You read the diff and run the tests | One evidence file per section, in `evidence/` next to the requirements | A separate checker agent runs each section's checks and writes down what it expected and found. Then the tests run again. Nothing to do. |
| **Try it** | `localhost` on your machine | A **Try it** link, in a comment on your issue and on your status page. For issue #1: {{SITE}}/GL1/ | Open it in your browser and use the change. Then reply on the issue: `approve`, or what's wrong. |
| **See where it stands** | Your terminal window | Your **status page**, and the comments on your issue | Open the status page any time: each request, its step, and an orange **Your turn** when it waits for you. |
| **Hand over** | You commit, push and open a merge request | A **merge request** in your project, linked from the issue and the status page | The factory opens it after your second `approve`. Our team reviews and merges it, and your app updates. |
| **What's recorded** | Your chat history, on your laptop | The issue, and `specs/` on the branch | Every step, check and approval stays on the issue. The requirements, plan and evidence stay in the repository. |
| **What you install** | Claude Code and a subscription | Nothing | A browser is enough. |

## The flow, in short

Everything you do happens on **one GitLab issue**: you write it, you read the
factory's comments on it, and you reply on it. Every link you need arrives as
one of those comments.

1. **You ask.** In GitLab, file an issue in plain words.
2. **It writes down what it understood.** Within a few minutes, a comment on
   your issue says **The factory is waiting for you** and links to
   `requirements.md`: short user stories, each with checks. Read it in GitLab,
   then reply on the issue with `approve`, or with what to change.
3. **It plans, builds and checks.** Nothing to do here. A **Factory progress**
   comment on your issue shows each step: the plan, each section built by a
   maker and verified by a separate checker, then the tests.
4. **You try it.** A new comment says the factory is waiting for you again,
   with a **Try it** link, such as {{SITE}}/GL1/ for issue #1. The link is on
   your status page too. Use the change in your browser, then reply on the
   issue with `approve`, or with what's wrong.
5. **It's handed over.** A comment links the **merge request**: the code, tests,
   requirements and evidence. Our team reviews and merges it, and your app
   updates.

A request usually takes 20 to 40 minutes of factory time, plus however long
it waits for your two approvals.

## Your logins

You have two, and we send them to you separately. Keep them private.

- **GitLab**, where you ask and approve: {{GITLAB}}. GitLab asks you to choose
  your own password the first time you sign in.
- **Your app and status page**, where you see results. Your browser asks for
  this login once, then remembers it.

## Your links

| What | Link |
|---|---|
| Your project | {{GITLAB}}/{{PROJECT}} |
| Ask for something | {{GITLAB}}/{{PROJECT}}/-/issues/new?issuable_template=Feature |
| Where your requests stand | {{SITE}}/status/ |
| Your app, as it is now | {{SITE}}/main/ |

### The links each request gets

Each request has its own links, made from its issue number. For your first
issue, **#1**, they are:

| What | Link for issue #1 | Where you'll find it |
|---|---|---|
| The conversation | {{GITLAB}}/{{PROJECT}}/-/issues/1 | Your project's **Issues** list, and the status page |
| What the factory understood | `{{GITLAB}}/{{PROJECT}}/-/blob/factory/GL1/specs/1-<your-title>/requirements.md` | The first **The factory is waiting for you** comment (the end of the link follows your issue's title) |
| **Try it** | {{SITE}}/GL1/ | The second **The factory is waiting for you** comment, and the status page |
| The finished work | {{GITLAB}}/{{PROJECT}}/-/merge_requests/1 | The last **Factory progress** comment, and the status page's **See the finished change** button |

For issue #2, change `1` to `2` (so `GL1` becomes `GL2`, and so on). The one
exception is the merge request: GitLab numbers those separately, so always
use the link in the comment rather than guessing it. The **Try it** page works
as soon as the factory posts the link, and keeps updating while that request
is open. It uses the same login as your status page. It shows that one
request's change. Your app at `/main/` changes only once our team merges it.

Your app starts as an empty page that says "Your app will appear here". Your
first request decides what it becomes.

## Asking for something

1. Open the **Ask for something** link above.
2. Give it a short title, for example *Build a CRM dashboard for my customers*.
3. Under **What should change**, write what you want, as you would in a
   Claude Code prompt but for the outcome, not the files. Under **How will we
   know it works?**, say what you'll check when you try it.
4. Leave the last line, `/label ~factory`, exactly as it is. It hands the issue
   to the factory.
5. Press **Create issue**.

One change per issue works best, the same as keeping a Claude Code session
focused on one task.

## Approving, and asking for changes

- **To approve**, reply `approve` **without a slash**. GitLab hides a comment
  that is only `/approve`, so the factory would never see it.
- **If the requirements aren't right**, don't approve: reply in plain words
  with what to change.
- **The status page** shows each request, its step, and an orange
  **Your turn** when it's waiting for you. Its button takes you to the issue.

## If you want to look under the hood

You're a Developer on the project, so you can clone it and read anything the
factory wrote:

- Work on a request happens on a branch called `factory/GL<issue number>`.
- Its requirements, plan and the checker's evidence are in `specs/` on that branch.
- The merge request links all of them.

Please don't push to `factory/*` branches yourself. Reply on the issue
instead, so the factory and the record stay in step.

## Ideas to start with

- Build a CRM dashboard: my customers in a table with company, deal stage and
  deal value, and totals at the top.
- Let me search my customers by name or company.
- Add a page for one customer with their notes.
- Show my deals as a board with a column for each stage.

## If something looks stuck

If nothing has happened for a while, or a comment says the factory stopped,
reply on the issue or get in touch with us. A person looks at it.
