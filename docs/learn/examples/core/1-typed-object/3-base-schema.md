# 3. Base Schema

<!-- example-source: examples/core/01_typed_object/03_base_schema.py -->

BaseSchema — Pydantic model with snake_case <-> camelCase aliasing.

Declare fields with `Field[T]`. At runtime `instance.field` returns `T`,
while `Class.field` returns a `FieldRef` (class-bound reference).

## Source

```{.python}
--8<-- "examples/core/01_typed_object/03_base_schema.py"
```

## Result

```text
id=1 name='SuperMan' is_active=True
<Hero.name>
{'id': 2, 'name': 'Spider', 'isActive': False}
```
