from datetime import datetime
from uuid import UUID

import pytest

from fastsprout.core import ReadDTO
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY
from fastsprout.testing.core import then, when

from .conftest import VisibilitySQLUser


class UserRead(ReadDTO, VisibilitySQLUser): ...


class ChildRead(UserRead): ...


class GrandchildRead(ChildRead): ...


@pytest.fixture(params=[UserRead, ChildRead, GrandchildRead])
def read_type(request: pytest.FixtureRequest) -> type[UserRead]:
    return request.param


@when("a read DTO is constructed from public fields")
def read(read_type: type[UserRead]) -> UserRead:
    return read_type(email="a@b.c", created_at=datetime(2026, 9, 17))


class TestSQLReadDTO:
    @then("read DTOs preserve their source, defaults and forbidden fields")
    def test_preserves_source_and_defaults(self, read: UserRead) -> None:
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

    @then("read DTOs are not mapped or registered as ORM entities")
    def test_has_no_orm_mapping(self, read: UserRead) -> None:
        assert "__mapper__" not in vars(type(read))
        assert "_sa_instance_state" not in vars(read)
        assert all(
            mapper.class_ is not type(read)
            for mapper in SQL_ENTITY_REGISTRY.mappers
        )

    @when("a forbidden field is accessed through the instance and class")
    def access_errors(self, read: UserRead, name: str) -> list[AttributeError]:
        errors: list[AttributeError] = []
        for target in (read, type(read)):
            try:
                getattr(target, name)
            except AttributeError as error:
                errors.append(error)
        return errors

    @pytest.mark.parametrize(
        "name", ["password", "password_hash", "last_login"]
    )
    @then("forbidden fields reject instance and class access")
    def test_forbidden_field_access(
        self, access_errors: list[AttributeError], name: str
    ) -> None:
        assert len(access_errors) == 2
        assert all(
            f"Field '{name}' not accessible" in str(error)
            for error in access_errors
        )

    @when("a forbidden field is passed to the read constructor")
    def constructor_error(
        self, read_type: type[UserRead], name: str
    ) -> AttributeError | None:
        try:
            read_type(
                email="a", created_at=datetime(2026, 9, 17), **{name: "secret"}
            )
        except AttributeError as error:
            return error
        return None

    @pytest.mark.parametrize(
        "name", ["password", "password_hash", "last_login"]
    )
    @then("read DTO construction rejects forbidden fields")
    def test_forbidden_constructor_argument(
        self, constructor_error: AttributeError | None, name: str
    ) -> None:
        assert isinstance(constructor_error, AttributeError)
        assert f"Field '{name}' not accessible" in str(constructor_error)
