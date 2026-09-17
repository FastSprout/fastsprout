from datetime import datetime
from uuid import UUID

import pytest

from fastsprout.core import ReadDTO
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY

from .conftest import VisibilitySQLUser


class UserRead(ReadDTO, VisibilitySQLUser): ...


class ChildRead(UserRead): ...


class GrandchildRead(ChildRead): ...


@pytest.fixture(params=[UserRead, ChildRead, GrandchildRead])
def read_type(request: pytest.FixtureRequest) -> type[UserRead]:
    return request.param


@pytest.fixture
def read(read_type: type[UserRead]) -> UserRead:
    return read_type(email="a@b.c", created_at=datetime(2026, 9, 17))


class TestSQLReadDTO:
    def test_preserves_source_and_defaults(self, read: UserRead):
        assert isinstance(read, VisibilitySQLUser)
        assert isinstance(read.id, UUID)
        assert read.email == "a@b.c"
        assert read.created_at == datetime(2026, 9, 17)
        assert type(read).__fastsprout_source__ is VisibilitySQLUser
        assert type(read).__fastsprout_forbidden__ == {
            "password",
            "password_hash",
            "last_login",
        }

    def test_has_no_orm_mapping(self, read: UserRead):
        assert "__mapper__" not in vars(type(read))
        assert "_sa_instance_state" not in vars(read)
        assert all(
            mapper.class_ is not type(read)
            for mapper in SQL_ENTITY_REGISTRY.mappers
        )

    @pytest.mark.parametrize(
        "name", ["password", "password_hash", "last_login"]
    )
    def test_forbidden_field_access(self, read: UserRead, name: str):
        for target in (read, type(read)):
            with pytest.raises(
                AttributeError, match=f"Field '{name}' not accessible"
            ):
                getattr(target, name)

    @pytest.mark.parametrize(
        "name", ["password", "password_hash", "last_login"]
    )
    def test_forbidden_constructor_argument(
        self, read_type: type[UserRead], name: str
    ):
        with pytest.raises(
            AttributeError, match=f"Field '{name}' not accessible"
        ):
            read_type(
                email="a", created_at=datetime(2026, 9, 17), **{name: "secret"}
            )
