# 10. DTO Visibility

<!-- example-source: examples/core/10_dto_visibility.py -->

Declare visibility on the entity's fields, then derive each DTO with a short class declaration. `UserRead` exposes readable fields, `UserCreate` exposes writable fields, and `UserUpdate` exposes both. The DTO remains a `User` subclass. Mypy and basedpyright reject direct access to forbidden attributes; the runtime guard also rejects dynamic access and forbidden constructor arguments.

Run from the repository root:

```bash
uv run --extra data-sql python examples/core/10_dto_visibility.py
```

## Source

```python
"""Declare fields once, then derive DTOs by choosing a visibility base.

Run: uv run --extra data-sql python examples/core/10_dto_visibility.py

Stock mypy and basedpyright check attribute access and assignment types.
DTO constructors check field names at runtime; validate input values at the
application boundary.
"""

from datetime import UTC, datetime
from typing import assert_type

from fastsprout.core import (
    BaseSchema,
    Field,
    InternalField,
    ReadDTO,
    ReadField,
    ReadWriteDTO,
    WriteDTO,
    WriteField,
)


class User(BaseSchema):
    email: Field[str]  # read and write
    password: WriteField[str]  # (1)!
    password_hash: InternalField[str]  # (2)!
    created_at: ReadField[datetime] = ReadField(
        default_factory=lambda: datetime.now(UTC)
    )


class UserRead(ReadDTO, User): ...  # (3)!


class UserCreate(WriteDTO, User): ...


class UserUpdate(ReadWriteDTO, User): ...


def show_forbidden_access(value: object, name: str) -> None:
    # Dynamic access demonstrates the runtime guard. Direct attribute access
    # to these fields also produces a checker error (see the comments below).
    try:
        getattr(value, name)  # (4)!
    except AttributeError as error:
        print(error)
    else:
        raise AssertionError(f"Field {name!r} should be inaccessible")


def main() -> None:
    read = UserRead(email="ada@example.com")
    create = UserCreate(email="ada@example.com", password="example-password")
    update = UserUpdate(email="ada@example.com", password="changed-password")

    assert_type(read.email, str)
    assert_type(read.created_at, datetime)
    assert_type(create.password, str)
    assert_type(update.password, str)
    assert_type(update.created_at, datetime)
    assert isinstance(read, User)
    read.email = "new@example.com"

    # Uncomment any of these to see mypy/basedpyright reject the access:
    # _ = read.password
    # _ = UserRead.password_hash
    # _ = create.created_at
    # read.email = 123

    print(read.email)
    show_forbidden_access(read, "password")
    show_forbidden_access(UserRead, "password_hash")
    show_forbidden_access(create, "created_at")
    show_forbidden_access(update, "password_hash")

    # ReadWriteDTO is the union of read and write fields, not a partial update:
    # required fields remain required, and internal fields stay forbidden.
    try:
        UserRead(email="ada@example.com", password="example-password")
    except AttributeError as error:
        print(error)
    else:
        raise AssertionError("The read constructor must reject password")


if __name__ == "__main__":
    main()
```

1. `WriteField` accepts input, but the field cannot appear in a read DTO.
2. `InternalField` stays on the entity and is excluded from every DTO.
3. The DTO inherits the entity's fields and types without redeclaring them.
4. `getattr` bypasses static checking, so the runtime guard rejects access.

## Result

The script prints the updated email, then five `AttributeError` messages for forbidden fields:

The errors cover read, write, and internal field restrictions, including a forbidden constructor argument.

```text
new@example.com
Field 'password' not accessible in DTO (operations: ['read'])
Field 'password_hash' not accessible in DTO (operations: ['read'])
Field 'created_at' not accessible in DTO (operations: ['write'])
Field 'password_hash' not accessible in DTO (operations: ['read', 'write'])
Field 'password' not accessible in DTO (operations: ['read'])
```
