# request-review factory

Reviews pull requests that carry the `factory-review` label. A script checks the process first; an agent reviews the code only if the process passed; one comment is posted on the request.

    python3 factory/flow.py init my-project-review --sample request-review --repo /path/to/your/repo

Set the rules in the factory editor, under Review rules.
