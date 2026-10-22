# 7. Bulk Dependencies

<!-- example-source: examples/actions/02_action_group/02_crud_service/07_bulk_dependencies.py -->

Combine batch access checks, model validation, and DataR dependencies.
Dependencies run once per chunk before its write. Service and router
dependencies share one DataR; deleting the batch is denied separately.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/07_bulk_dependencies.py"
```

## Result

```text
Action: bulk_create
Rejected: Power must be non-negative
After rejected batch: 0
Action: bulk_create
Backend: bulk_create
Created: Batman
Created: Robin
Action: bulk_create
Backend: bulk_create
Created: Batgirl
Rejected: Deleting batches is forbidden
Remaining: 3
```
