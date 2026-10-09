# 3. Base Schema

<!-- example-source: examples/core/01_typed_object/03_base_schema.py -->

BaseSchema — Pydantic model with snake_case <-> camelCase aliasing.

Declare fields with `Field[T]`. At runtime `instance.field` returns `T`,
while `Class.field` returns a `FieldRef` (class-bound reference).

## Source

```python
"""BaseSchema — Pydantic model with snake_case <-> camelCase aliasing.

Declare fields with `Field[T]`. At runtime `instance.field` returns `T`,
while `Class.field` returns a `FieldRef` (class-bound reference).
"""

from fastsprout.core.fields import Field
from fastsprout.core.schema import BaseSchema


class Hero(BaseSchema):
    id: Field[int]
    name: Field[str]
    is_active: Field[bool]


def main() -> None:
    hero = Hero(id=1, name="SuperMan", is_active=True)

    # Class access returns FieldRef, not the raw descriptor.
    ref = Hero.name

    # camelCase aliasing on input/output.
    payload = {"id": 2, "name": "Spider", "isActive": False}
    parsed = Hero.model_validate(payload)

    print(hero)
    print(ref)
    print(parsed.model_dump(by_alias=True))


if __name__ == "__main__":
    main()
```

## Result

```text
id=1 name='SuperMan' is_active=True
<Hero.name>
{'id': 2, 'name': 'Spider', 'isActive': False}
```
