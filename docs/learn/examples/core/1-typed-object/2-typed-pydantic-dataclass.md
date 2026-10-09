# 2. Typed Pydantic Dataclass

<!-- example-source: examples/core/01_typed_object/02_typed_pyd_dataclass.py -->

@typed_pydantic_dataclass — Pydantic dataclass + Field[T] descriptors.

Lighter than BaseSchema (no BaseModel machinery) but keeps runtime
validation through Pydantic.

## Source

```python
"""@typed_pydantic_dataclass — Pydantic dataclass + Field[T] descriptors.

Lighter than BaseSchema (no BaseModel machinery) but keeps runtime
validation through Pydantic.
"""

from pydantic import TypeAdapter, ValidationError

from fastsprout.core.decorators import typed_pydantic_dataclass
from fastsprout.core.fields import Field


@typed_pydantic_dataclass
class User:
    field_int: Field[int]
    field_str: Field[str]


def main() -> None:
    user = User(field_int=1, field_str="alice")
    print(user)

    try:
        TypeAdapter(User).validate_python(
            {"field_int": "not an int", "field_str": "bob"}
        )
    except ValidationError as e:
        print("Validation rejected bad payload:", e.errors()[0]["loc"])


if __name__ == "__main__":
    main()
```

## Result

```text
User(field_int=1, field_str='alice')
Validation rejected bad payload: ('field_int',)
```
