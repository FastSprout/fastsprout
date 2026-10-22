# 26. Field Predicate Writes

<!-- example-source: examples/actions/02_action_group/02_crud_service/26_field_predicate_writes.py -->

Use field conditions or SQLQuery to stream and write matching records.
All conditions are combined with AND: a record must match every condition.
Pass either a SQLQuery with its conditions or field predicates directly.
DataS preserves Query entity and visibility checks and returns affected counts.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/26_field_predicate_writes.py"
```

## Result

```text
Updated: 1
Matched: Robin 60
Batgirl 50
Robin 60
Batman 80
Deleted: 1
Remaining: 2
SQLQuery updated: 1
SQLQuery deleted: 1
Remaining: 1
```
