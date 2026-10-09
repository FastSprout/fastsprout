# 1. Typed Dataclass

<!-- example-source: examples/core/01_typed_object/01_typed_dataclass.py -->

@typed_dataclass — stdlib @dataclass + Field[T] descriptors.

Same Field[T] declaration ergonomics as BaseSchema, no Pydantic overhead,
no runtime validation. Useful for internal value objects.

## Source

```python
"""@typed_dataclass — stdlib @dataclass + Field[T] descriptors.

Same Field[T] declaration ergonomics as BaseSchema, no Pydantic overhead,
no runtime validation. Useful for internal value objects.
"""

from fastsprout.core.decorators import typed_dataclass
from fastsprout.core.fields import Field


@typed_dataclass
class Point:
    x: Field[int]
    y: Field[int]
    label: Field[str]


def main() -> None:
    p = Point(x=1, y=2, label="origin-ish")

    print(p)
    print(Point.x)


if __name__ == "__main__":
    main()
```

## Result

```text
Point(x=1, y=2, label='origin-ish')
<Point.x>
```
