# 7. Connect actions in a workflow

One operation can have several stages. Here, preparing a task must run the
shared title check and normalization before a formatting step uses the result.
Compose those stages as a reusable workflow.

The example reuses `NewTask`, `TaskDraft`, and the checked preparation action
from the earlier steps. The new operation accepts a `TaskDraft` and returns
another `TaskDraft` with an uppercase title.
Save this program as `docs_src/tutorial/workflows.py`.

<!-- example-source: docs_src/tutorial/workflows.py -->

```{.python}
--8<-- "docs_src/tutorial/workflows.py"
```

Run it from your tutorial directory:

```bash
python -m docs_src.tutorial.workflows
```

## Result

```text
WRITE DOCUMENTATION
```

## Follow the result through the steps

`Workflow(prepare_task)` starts with an action that takes `NewTask` and returns
`TaskDraft`. `.then(uppercase_title)` connects that result to the next action's
input. Their types remain available to the type checker.

Calling the workflow returns an async generator. Iteration starts execution,
runs the shared check, and passes each result to the next step. This example
emits one draft; the same interface can handle steps that emit no result or
multiple results.

A workflow packages the composition as one callable operation. As the process
grows, it can include other workflows, concurrent forks, and typed branches.
Continue with the [workflow guide](../guide/actions.md#workflows) for those
patterns, or return to the [Data guide](../guide/data.md) for entity-service
schemas, bulk operations, and joins.

[Previous: Queries](queries.md) · [Tutorial start](../getting-started.md)
