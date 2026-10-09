# 2. SQL

<!-- example-source: examples/core/04_dto/02_sql.py -->

Derive a DTO from a SQL entity and extend it with ordinary inheritance.

The UUID and visibility of inherited fields are preserved. Creating DTO
classes does not register additional SQLAlchemy mappings. DTO instances are
data containers; use the source entity when persisting to the database.

## Source

```python
"""Derive a DTO from a SQL entity and extend it with ordinary inheritance.

The UUID and visibility of inherited fields are preserved. Creating DTO
classes does not register additional SQLAlchemy mappings. DTO instances are
data containers; use the source entity when persisting to the database.
"""

from datetime import UTC, datetime
from typing import assert_type
from uuid import UUID, uuid4

from sqlmodel import Field as SQLField

from fastsprout.core import Field, InternalField, ReadDTO, ReadField
from fastsprout.data.backend.sql import SQLEntity


class DefaultSQLEntity(SQLEntity[UUID], table=False):
    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    last_login: InternalField[datetime | None] = InternalField[datetime | None](
        default=None
    )


class User(DefaultSQLEntity):
    email: Field[str]
    password_hash: InternalField[str]
    created_at: ReadField[datetime] = ReadField(
        default_factory=lambda: datetime.now(UTC)
    )


class UserRead(ReadDTO, User): ...


class UserSummary(UserRead):
    def label(self) -> str:
        return f"{self.id}: {self.email}"


def display(user: UserRead) -> str:
    assert_type(user.id, UUID)
    assert_type(user.created_at, datetime)
    return user.email


def main() -> None:
    read = UserRead(email="ada@example.com")
    summary = UserSummary(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        email="grace@example.com",
    )

    print(display(read))
    print(display(summary))
    print(summary.label())

    # Both checkers reject direct access, including on the subclass:
    # _ = summary.last_login
    # _ = UserSummary.password_hash

    for name in ("last_login", "password_hash"):
        try:
            getattr(summary, name)
        except AttributeError as error:
            print(error)


if __name__ == "__main__":
    main()
```

## Result

```text
ada@example.com
grace@example.com
00000000-0000-0000-0000-000000000001: grace@example.com
Field 'last_login' not accessible in DTO (operations: ['read'])
Field 'password_hash' not accessible in DTO (operations: ['read'])
```
