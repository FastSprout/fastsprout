# 1. Base Schema

Define a schema once with `Field[T]`. Instances expose typed values; access through the class returns a `FieldRef` that identifies the field and its owner. `BaseSchema` also accepts camelCase input and can emit camelCase aliases.

Run from the repository root:

```bash
uv run --extra data-sql python examples/core/01_base_schema.py
```

## Source

```python
--8<-- "examples/core/01_base_schema.py"
```

## Result

The script prints the validated hero and the reference to `Hero.name`:

```text
id=1 name='SuperMan' is_active=True
<Hero.name>
```
