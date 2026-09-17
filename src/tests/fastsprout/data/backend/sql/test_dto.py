from datetime import datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlmodel import Field as SQLField
from sqlmodel import Session, create_engine

from fastsprout.core import (
    Field,
    InternalField,
    ReadDTO,
    ReadField,
    WriteField,
)
from fastsprout.data.backend.sql import SQLEntity
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY


class DefaultSQLEntity(SQLEntity[UUID], table=False):
    id: Field[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    last_login: InternalField[datetime | None] = InternalField[datetime | None](
        default=None
    )


class VisibilitySQLUser(DefaultSQLEntity):
    email: Field[str]
    password: WriteField[str]
    password_hash: InternalField[str]
    created_at: ReadField[datetime]


@pytest.mark.parametrize("depth", [0, 1, 2])
def test_sql_dto_preserves_inheritance_without_mapping_a_table(
    depth: int,
) -> None:
    mappers_before = set(SQL_ENTITY_REGISTRY.mappers)

    class UserRead(ReadDTO, VisibilitySQLUser): ...

    read_type = UserRead
    for level in range(depth):
        read_type = type(f"ChildRead{level}", (read_type,), {})

    read = read_type(email="a@b.c", created_at=datetime.now())
    assert isinstance(read.id, UUID)
    assert isinstance(read, VisibilitySQLUser)
    assert read.email == "a@b.c"
    assert read_type.__fastsprout_source__ is VisibilitySQLUser
    assert read_type.__fastsprout_forbidden__ == {
        "password",
        "password_hash",
        "last_login",
    }
    assert set(SQL_ENTITY_REGISTRY.mappers) == mappers_before
    assert "__mapper__" not in vars(read_type)
    assert "_sa_instance_state" not in vars(read)
    for name in read_type.__fastsprout_forbidden__:
        for obj in (read, read_type):
            with pytest.raises(AttributeError, match="not accessible"):
                getattr(obj, name)
        with pytest.raises(AttributeError, match="not accessible"):
            read_type(email="a", created_at=datetime.now(), **{name: "secret"})


def test_sql_entity_retains_visibility_descriptors_and_persistence() -> None:
    assert isinstance(vars(VisibilitySQLUser)["password"], WriteField)
    assert isinstance(vars(VisibilitySQLUser)["last_login"], InternalField)
    assert isinstance(VisibilitySQLUser.password.orm, InstrumentedAttribute)
    engine = create_engine("sqlite://")
    VisibilitySQLUser.__table__.create(engine)
    try:
        with Session(engine) as session:
            user = VisibilitySQLUser(
                email="a",
                password="secret",
                password_hash="hash",
                created_at=datetime.now(),
            )
            identifier = user.id
            session.add(user)
            session.commit()
        with Session(engine) as session:
            loaded = session.get(VisibilitySQLUser, identifier)
            assert loaded is not None
            assert loaded.password == "secret"
            assert loaded.password_hash == "hash"
            assert loaded.last_login is None
    finally:
        engine.dispose()
