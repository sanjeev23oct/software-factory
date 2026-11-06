# CRM

Your CRM, built by the [software factory](https://github.com/sanjeev23oct/software-factory)
one issue at a time. File an issue with the **Feature** template and the
factory takes it from there: it writes the requirements, waits for your
`/approve`, builds the change with a separate checker, posts a link where you
can try it, and opens a merge request when you approve again.

Everything the factory does shows up as comments on your issue.

## Ideas to start with

- Build a CRM dashboard: my customers in a table with company, contact, deal stage and deal value, and totals at the top.
- Let me search customers by name or company.
- Add a page for one customer with their notes and activity.
- Show deals as a pipeline board by stage.

## For developers

No build step and no dependencies: plain HTML, CSS and JavaScript modules.

    python3 -m http.server 8081     # then open http://127.0.0.1:8081
    node --test                     # run the tests
