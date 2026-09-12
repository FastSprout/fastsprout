"""@typed_pydantic_dataclass — Pydantic dataclass + Field[T] descriptors.

Lighter than BaseSchema (no BaseModel machinery) but keeps runtime
validation through Pydantic.
"""

from pydantic import ValidationError

from fastsprout.core.decorators import typed_pydantic_dataclass
from fastsprout.core.fields import Field


@typed_pydantic_dataclass
class User:
    field_int: Field[int]
    field_str: Field[str]


def main() -> None:
    user = User(field_int=1, field_str="alice")
    assert user.field_int == 1
    assert user.field_str == "alice"

    try:
        User(field_int="not an int", field_str="bob")  # type: ignore[arg-type]
    except ValidationError as e:
        print("Validation rejected bad payload as expected:")
        print(e)
    else:
        raise AssertionError("expected ValidationError")


if __name__ == "__main__":
    main()
