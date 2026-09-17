"""DTO visibility with an unmodified Pylance/pyright/basedpyright.

Run: uv run --extra data-sql python docs/dto_visibility.py

Fields are declared only on the entity. Each DTO has a short class declaration
so it is a real type usable in annotations. The visibility base goes first;
the library selects the DTO constructor automatically.
Constructor names are checked at runtime; attribute access is checked statically.
See dto_visibility.md for the API and limitations.
"""

from datetime import datetime
from typing import assert_type
from uuid import UUID, uuid4

from sqlmodel import Field as SQLField

from fastsprout.core import (
    Field,
    InternalField,
    ReadDTO,
    ReadField,
    ReadWriteDTO,
    WriteDTO,
    WriteField,
)
from fastsprout.data.backend.sql import SQLEntity


class DefaultSQLEntity(SQLEntity[UUID], table=False):
    id: Field[UUID] = SQLField(default_factory=uuid4, primary_key=True)


class User(DefaultSQLEntity):
    email: Field[str]
    password: WriteField[str]
    password_hash: InternalField[str]
    created_at: ReadField[datetime]


class UserRead(ReadDTO, User): ...


class UserCreate(WriteDTO, User): ...


class UserUpdate(ReadWriteDTO, User): ...


class S(UserRead): ...


def display(user: UserRead) -> str:
    assert_type(user.id, UUID)
    assert_type(user.email, str)
    assert_type(user.created_at, datetime)
    return user.email


# The checker rejects these (tested separately as expected diagnostics):
# read.password
# read.password_hash
# read.password = "secret"
# UserRead.password_hash


def main() -> None:
    read = UserRead(email="a@b.c", created_at=datetime.now())
    read_s = S(email="a@b.c", created_at=datetime.now())
    create = UserCreate(email="a@b.c", password="secret")
    assert_type(create.password, str)
    print(read)  # noqa: T201
    print(read_s)  # noqa: T201
    print(display(read))  # noqa: T201
    print(display(read_s))  # noqa: T201
    for name in ("password", "password_hash"):
        try:
            getattr(read, name)
        except AttributeError as error:
            print(error)  # noqa: T201
    try:
        UserRead(email="a@b.c", created_at=datetime.now(), password="secret")
    except AttributeError as error:
        print(error)  # noqa: T201

    try:
        S(email="a@b.c", created_at=datetime.now(), password="secret")
    except AttributeError as error:
        print(error)  # noqa: T201


if __name__ == "__main__":
    main()
