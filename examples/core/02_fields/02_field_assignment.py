"""Field.set(value) -> FieldAssignment[T].

Use FieldAssignment lists as partial-update payloads for repositories
or update endpoints.
"""

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

    # From a class attribute (Hero.is_active is a FieldRef, .set works too).
    toggled = Hero.is_active.set(False)

    # Bundle changes for a hypothetical repo.update call.
    changes: list[FieldAssignment[str] | FieldAssignment[bool]] = [
        assignment,
        toggled,
    ]
    for change in changes:
        print(change)


if __name__ == "__main__":
    main()
