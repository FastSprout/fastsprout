"""@typed_dataclass — stdlib @dataclass + Field[T] descriptors.

Same Field[T] declaration ergonomics as BaseSchema, no Pydantic overhead,
no runtime validation. Useful for internal value objects.
"""

from fastsprout.core.decorators import typed_dataclass
from fastsprout.core.fields import Field
from fastsprout.core.fields.field_ref import FieldRef


@typed_dataclass
class Point:
    x: Field[int]
    y: Field[int]
    label: Field[str]


def main() -> None:
    p = Point(x=1, y=2, label="origin-ish")

    assert p.x == 1
    assert p.label == "origin-ish"

    # __eq__ / __repr__ from dataclass still work.
    assert p == Point(x=1, y=2, label="origin-ish")
    assert "Point(x=1" in repr(p)

    # Class-level access returns FieldRef.
    assert isinstance(Point.x, FieldRef)
    assert Point.x.name == "x"

    print(p)


if __name__ == "__main__":
    main()
