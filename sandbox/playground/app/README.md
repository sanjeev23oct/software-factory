# Software factory playground

Your app, built by the [software factory](https://github.com/sanjeev23oct/software-factory)
one request at a time. It starts as an empty page.

1. File an issue with the **Feature** template. Say what you want the way you
   would to a colleague.
2. The factory writes down what it understood and asks you to reply `approve`.
3. It builds the change and has a separate checker verify it.
4. It posts a **Try it** link. Use the change, then reply `approve` again.
5. It opens a merge request with the code, the tests and the evidence.

Everything shows up as comments on your issue. Reply `approve` without a slash:
GitLab swallows `/approve` on an issue.

## Ideas to start with

- Build a CRM dashboard: my customers in a table with company, deal stage and deal value, and totals at the top.
- Make a simple landing page for my product with a sign-up form.
- Show my team's tasks as a board with To do, Doing and Done.
- Add a page that turns a list of expenses into a monthly summary.

## For developers

No build step and no dependencies: plain HTML, CSS and JavaScript modules.

    python3 -m http.server 8081     # then open http://127.0.0.1:8081
    node --test                     # run the tests
