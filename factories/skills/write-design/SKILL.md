---
name: write-design
description: Write design.md for a work item whose requirements are approved: data, API and UI decisions, explicit enough to build from.
---
# write-design

Write exactly one file: `<spec folder>/design.md`. Change nothing else. `requirements.md` is approved; do not edit it.

Read the code first and cite it as `path:line`. Cover only the layers the work touches, each as its own section:

- **Data**: tables or stored shapes, column types, constraints, and how existing data keeps working.
- **API / backend**: endpoints or functions with request and response shapes, status codes, and error bodies.
- **UI**: screens, states (loading, empty, error), and which API calls each makes.

Then **Decisions**: each real trade-off, the option chosen, and the one rejected. Refer to acceptance criteria by number instead of restating them. Keep it proportional: a small change gets a short design.
