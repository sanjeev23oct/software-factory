# Organisation knowledge: reuse, don't rebuild

Agents read the code of the project they work on, but not what the rest of the organisation already
runs. Without help, a request that needs to send an email or store an attachment gets a new email
sender or a new document table. The organisation knowledge prevents that: a short catalog of the
shared services and platforms, which every agent must check before designing anything cross-cutting.

## Where it lives

`knowledge/` in the factory project, next to `targets/` (for us, `itb/factory-pipelines/knowledge/`).
It applies to every pipeline in that project. `FACTORY_KNOWLEDGE_DIR` points somewhere else.

```
knowledge/
├── INDEX.md                 which service for which need: the first thing agents read
└── services/
    ├── notification-service.md
    ├── document-service.md
    └── …
```

The factory turns it on when `knowledge/INDEX.md` exists.

## What agents do with it

| Stage | Rule |
|---|---|
| Requirements | A section **Existing services used** names the catalogued service for each cross-cutting need. If nothing fits, it goes under *Needs clarification*: the person decides, not the agent |
| Plan | Tasks **call** the service the way its entry says; no task rebuilds it |
| Build | The maker integrates using the entry's client, configuration and endpoints |
| AI review | Code that rebuilds a catalogued service is a **blocking** finding, naming the service to use |

## Writing an entry

Short and factual: agents follow it literally. One file per service:

```markdown
# Notification service

**Use it for:** sending email, SMS and push notifications from any application.
**Never build instead:** an SMTP client, an SMS gateway integration, a notifications table.

## How to call it
- Base URL: dev `https://…`, UAT `https://…`, prod `https://…` (from configuration key `Notification:BaseUrl`)
- Auth: service token from configuration `Notification:Token`, sent as `Authorization: Bearer …`
- Endpoints: `POST /api/v1/notifications` with `{channel, to, template, data}`

## In .NET / in React
How existing projects call it, with a link to one as the example to copy.

## Owner and docs
Team, contact, repository, API documentation.
```

`INDEX.md` maps needs to entries in one table, so an agent finds the right one quickly:

| Need | Use | Entry |
|---|---|---|
| Send email, SMS or push | Notification service | [services/notification-service.md](services/notification-service.md) |

## Keeping it right

Treat it like code: changes by merge request, reviewed by the owners of the services. A wrong entry
makes every agent wrong in the same way; a missing one makes them build duplicates. When the AI
reviewer or a person at a gate finds an agent rebuilt something, add the entry that would have
prevented it.
