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
    # From an unbound Field instance.
    assignment = Field[str]("name").set("Spider")
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
