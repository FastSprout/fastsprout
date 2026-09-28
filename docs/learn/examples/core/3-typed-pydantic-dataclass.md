# 3. Typed Pydantic Dataclass

<!-- example-source: examples/core/03_typed_pyd_dataclass.py -->

Use `@typed_pydantic_dataclass` when a dataclass also needs input validation. The script constructs a valid user, then deliberately passes text to an integer field.

Run from the repository root:

```bash
uv run --extra data-sql python examples/core/03_typed_pyd_dataclass.py
```

## Source

```python
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
        print("Validation rejected bad payload:", e.errors()[0]["loc"])
    else:
        raise AssertionError("expected ValidationError")


if __name__ == "__main__":
    main()
```

## Result

The valid user is accepted. The invalid value raises `ValidationError`; the example prints the rejected field:

```text
Validation rejected bad payload: ('field_int',)
```
