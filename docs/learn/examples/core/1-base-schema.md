# 1. Base Schema

<!-- example-source: examples/core/01_base_schema.py -->

Define a schema once with `Field[T]`. Instances expose typed values; access through the class returns a `FieldRef` that identifies the field and its owner. `BaseSchema` also accepts camelCase input and can emit camelCase aliases.

Run from the repository root:

```bash
uv run --extra data-sql python examples/core/01_base_schema.py
```

## Source

```python
"""BaseSchema — Pydantic model with snake_case <-> camelCase aliasing.

Declare fields with `Field[T]`. At runtime `instance.field` returns `T`,
while `Class.field` returns a `FieldRef` (class-bound reference).
"""

from fastsprout.core.fields import Field
from fastsprout.core.fields.field_ref import FieldRef
from fastsprout.core.schema import BaseSchema


class Hero(BaseSchema):
    id: Field[int]
    name: Field[str]
    is_active: Field[bool]


def main() -> None:
    hero = Hero(id=1, name="SuperMan", is_active=True)

    assert hero.name == "SuperMan"
    assert hero.is_active is True

    # Class access returns FieldRef, not the raw descriptor.
    ref = Hero.name
    assert isinstance(ref, FieldRef)
    assert ref.name == "name"
    assert ref.entity_cls is Hero

    # camelCase aliasing on input/output.
    payload = {"id": 2, "name": "Spider", "isActive": False}
    parsed = Hero.model_validate(payload)
    assert parsed.is_active is False
    assert parsed.model_dump(by_alias=True)["isActive"] is False

    print(hero)
    print(ref)


if __name__ == "__main__":
    main()
```

## Result

The script prints the validated hero and the reference to `Hero.name`:

```text
id=1 name='SuperMan' is_active=True
<Hero.name>
```
