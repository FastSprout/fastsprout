# 2. Share a check between actions

A task title must contain something besides spaces. Preparing a task and
previewing it should enforce the same rule. Attach one dependency to both
actions so each caller gets that check automatically.

This program reuses `NewTask`, `TaskDraft`, and title normalization from
[the first step](../getting-started.md). The new pieces are `require_title`
and `Depends`.

<!-- example-source: docs_src/tutorial/shared_checks.py -->

```{.python}
--8<-- "docs_src/tutorial/shared_checks.py"
```

Run it from the repository root:

```bash
uv run python -m docs_src.tutorial.shared_checks
```

## Result

```text
Prepared: Write documentation
Preview: Task: Write documentation
Rejected: Task title cannot be empty
```

## Why attach a dependency?

`Depends(require_title)` tells the action to run the check before its body.
The dependency requests `payload` by the same argument name used in the action.
If the check raises, the action stops and the caller receives the exception.

Both actions reuse the same check and the original normalization operation.
An endpoint or worker calls an action; it does not need to remember to call
`require_title` separately. Change the rule in one function when the feature's
requirements change.

The `try` block handles the error for this demonstration. In an application,
the caller decides how to report it, such as a rejected command or an HTTP
error response.

Try giving `preview_task` an empty title too. Its dependency enforces the same
rule. Next, group these two operations in a service.

[Previous: Your first action](../getting-started.md) ·
[Next: Group related operations](services.md)
