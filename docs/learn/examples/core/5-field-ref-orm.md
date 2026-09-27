# 5. Field Ref ORM

This example builds a small SQLModel bridge to show what `HasOrm` exposes. A class-level `FieldRef.orm` points to SQLAlchemy's mapped attribute, which can be used in SQL expressions; `.set()` still creates a plain field assignment.

Run from the repository root:

```bash
uv run --extra data-sql python examples/core/05_field_ref_orm.py
```

## Source

```python
--8<-- "examples/core/05_field_ref_orm.py"
```

## Result

The assertion checks that `Hero.name.orm` is an `InstrumentedAttribute`. The script prints:

```text
FieldAssignment(name='name', value='Spider')
```
