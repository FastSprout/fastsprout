# 1. Field Ref ORM

<!-- example-source: examples/core/02_fields/01_field_ref_orm.py -->

HasOrm + FieldRef.orm with SQLModel.

Requires `sqlmodel` (already in the dev extras).

`Hero.id.orm` returns the SQLAlchemy `InstrumentedAttribute` at runtime.
The Field overload types it as `Mapped[int]` in stock mypy and pyright.
Custom wrappers retain the type arguments declared in HasOrm; for example,
HasOrm[CustomOrm[Any]] exposes CustomOrm[Any] for every field.

## Source

```{.python}
--8<-- "examples/core/02_fields/01_field_ref_orm.py"
```

## Result

```text
SuperMan
Hero.name
FieldAssignment(name='name', value='Spider')
```
