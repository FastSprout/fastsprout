# 4. Field Assignment

Call `.set(value)` on a class-level field reference to build a `FieldAssignment`. This captures the field name and new value without mutating an entity, so a repository can accept a list of partial changes.

Run from the repository root:

```bash
uv run --extra data-sql python examples/core/04_field_assignment.py
```

## Source

```python
--8<-- "examples/core/04_field_assignment.py"
```

## Result

```text
FieldAssignment(name='name', value='Spider')
FieldAssignment(name='is_active', value=False)
```
