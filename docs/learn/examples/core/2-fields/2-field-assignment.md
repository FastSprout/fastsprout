# 2. Field Assignment

<!-- example-source: examples/core/02_fields/02_field_assignment.py -->

Field.set(value) -> FieldAssignment[T].

Use FieldAssignment lists as partial-update payloads for repositories
or update endpoints.

## Source

```{.python}
--8<-- "examples/core/02_fields/02_field_assignment.py"
```

## Result

```text
FieldAssignment(name='name', value='Spider')
FieldAssignment(name='is_active', value=False)
```
