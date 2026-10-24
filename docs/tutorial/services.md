# 3. Group related operations

The task feature now has preparation and preview operations. Give callers one
service object for the feature. Reuse the checked actions from
[the previous step](shared-checks.md), including their existing dependencies.
Save this program as `docs_src/tutorial/services.py`.

<!-- example-source: docs_src/tutorial/services.py -->

```{.python}
--8<-- "docs_src/tutorial/services.py"
```

Run it from your tutorial directory:

```bash
python -m docs_src.tutorial.services
```

## Result

```text
Prepared: Write documentation
Preview: Task: Write documentation
Rejected: Task title cannot be empty
```

## What the service adds

`TaskService` inherits from `Service`. Its `prepare` and `preview` attributes
reuse the actions you already wrote. Their input and result types remain
available, and the shared title check still runs. The failed preview call
shows that grouping an action preserves its dependency behavior.

Callers can now receive a `TaskService` and call the operations of the task
feature through that object. A service can also define public async methods,
request collaborators with `Depends`, and call other services. Those options
are covered in the [Actions guide](../guide/actions.md#services-and-dependency-injection).

Use `Service` to organize application behavior. When the next feature needs
standard operations for a stored entity, `DataS` supplies those operations.

[Previous: Shared checks](shared-checks.md) ·
[Next: Store and retrieve tasks](entity-operations.md)
