# 6. Bulk Operations

<!-- example-source: examples/actions/02_action_group/02_crud_service/06_bulk_operations.py -->

Create, update, patch, and delete batches from single-use iterables.
Create uses a generator, update and delete use async generators, and PATCH
uses (identifier, payload) pairs. Results keep the order of their inputs.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/06_bulk_operations.py"
```

## Result

```text
Created: [('Batman', 100), ('Robin', 100)]
Updated: [('Batman', 101), ('Robin', 101)]
Updated by key: [('Batman', 150), ('Robin', 150)]
Patched: [('Batman', 200), ('Robin', 200)]
Deleted: 2
Remaining: 0
```
