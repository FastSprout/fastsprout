"""Derive a DTO from a SQL entity and extend it with ordinary inheritance.

Run: uv run --extra data-sql python examples/core/11_dto_sql.py

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
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY


class DefaultSQLEntity(SQLEntity[UUID], table=False):
    id: Field[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    last_login: InternalField[datetime | None] = InternalField[datetime | None](
        default=None
    )


class User(DefaultSQLEntity):
    email: Field[str]
    password_hash: InternalField[str]
    created_at: ReadField[datetime] = ReadField(
        default_factory=lambda: datetime.now(UTC)
    )


MAPPERS_BEFORE_DTOS = set(SQL_ENTITY_REGISTRY.mappers)


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
    summary = UserSummary(email="grace@example.com")

    assert isinstance(read.id, UUID)
    assert isinstance(summary.id, UUID)
    assert read.id != summary.id
    assert isinstance(summary, User)
    assert set(SQL_ENTITY_REGISTRY.mappers) == MAPPERS_BEFORE_DTOS
    assert "_sa_instance_state" not in vars(summary)

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
        else:
            raise AssertionError(f"Field {name!r} should be inaccessible")


if __name__ == "__main__":
    main()
