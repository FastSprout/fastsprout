# 4. Field Assignment

<!-- example-source: examples/core/04_field_assignment.py -->

Call `.set(value)` on a class-level field reference to build a `FieldAssignment`. This captures the field name and new value without mutating an entity, so a repository can accept a list of partial changes.

Run from the repository root:

```bash
uv run --extra data-sql python examples/core/04_field_assignment.py
```

## Source

```python
"""Field.set(value) -> FieldAssignment[T].

Use FieldAssignment lists as partial-update payloads for repositories
or update endpoints.
"""

from typing import Any

from fastsprout.core.fields import Field
from fastsprout.core.fields.field_assigment import FieldAssignment
from fastsprout.core.schema import BaseSchema


class Hero(BaseSchema):
    id: Field[int]
    name: Field[str]
    is_active: Field[bool]


def main() -> None:
    # From a field bound to the entity class.
    assignment = Hero.name.set("Spider")
    assert isinstance(assignment, FieldAssignment)
    assert assignment.name == "name"
    assert assignment.value == "Spider"

    # From a class attribute (Hero.is_active is a FieldRef, .set works too).
    toggled = Hero.is_active.set(False)
    assert toggled == FieldAssignment("is_active", False)

    # Bundle changes for a hypothetical repo.update call.
    changes: list[FieldAssignment[Any]] = [
        Hero.name.set("Spider"),
        Hero.is_active.set(False),
    ]
    for change in changes:
        print(change)


if __name__ == "__main__":
    main()
```

## Result

```text
FieldAssignment(name='name', value='Spider')
FieldAssignment(name='is_active', value=False)
```
