from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from fastsprout.core import (
    BaseSchema,
    Field,
    InternalField,
    ReadDTO,
    ReadField,
    ReadWriteDTO,
    WriteDTO,
    WriteField,
    dto,
)


class User(BaseSchema):
    id: Field[UUID] = Field(default_factory=uuid4)
    email: Field[str]
    password: WriteField[str]
    password_hash: InternalField[str]
    created_at: ReadField[datetime]
    tags: Field[list[str]] = Field(default=[])


class UserRead(ReadDTO, User): ...


class UserCreate(WriteDTO, User): ...


class UserUpdate(ReadWriteDTO, User): ...


class ChildRead(UserRead):
    def display(self) -> str:
        return self.email


class GrandchildRead(ChildRead): ...


@pytest.fixture(params=[UserRead, ChildRead, GrandchildRead])
def read(request: pytest.FixtureRequest) -> UserRead:
    return request.param(email="a@b.c", created_at=datetime(2026, 9, 17))


def test_read_preserves_values_defaults_and_source(read: UserRead) -> None:
    assert read.email == "a@b.c"
    assert read.created_at == datetime(2026, 9, 17)
    assert isinstance(read.id, UUID)
    assert isinstance(read, User)
    read_type = type(read)
    assert read_type.__fastsprout_source__ is User
    assert read_type.__fastsprout_operations__ == {"read"}
    assert read_type.__fastsprout_forbidden__ == {"password", "password_hash"}
    other = read_type(email="b@c.d", created_at=read.created_at)
    read.tags.append("mine")
    assert other.tags == []
    assert other.id != read.id
    read.email = "changed@example.com"
    assert read.email == "changed@example.com"


@pytest.mark.parametrize("name", ["password", "password_hash"])
def test_read_guards_all_normal_access(read: UserRead, name: str) -> None:
    read_type = type(read)
    for obj in (read, read_type):
        with pytest.raises(
            AttributeError, match=f"Field '{name}' not accessible"
        ):
            getattr(obj, name)
    with pytest.raises(AttributeError, match="not accessible"):
        setattr(read, name, "secret")
    with pytest.raises(AttributeError, match="not accessible"):
        object.__setattr__(read, name, "secret")
    with pytest.raises(AttributeError, match="not accessible"):
        delattr(read, name)
    with pytest.raises(AttributeError, match="not accessible"):
        read_type(email="a", created_at=datetime.now(), **{name: "secret"})
    assert not hasattr(read, name)
    assert name not in vars(read)


def test_write_and_union_visibility() -> None:
    create = UserCreate(email="a", password="secret")
    assert create.password == "secret"
    for name in ("created_at", "password_hash"):
        with pytest.raises(AttributeError, match="not accessible"):
            getattr(create, name)
    update = UserUpdate(email="a", password="secret", created_at=datetime.now())
    assert update.password == "secret"
    assert isinstance(update.created_at, datetime)
    internal_name = "password_hash"
    with pytest.raises(AttributeError, match="not accessible"):
        getattr(update, internal_name)


def test_source_retains_internal_fields_and_validation() -> None:
    user = User(
        email="a",
        password="secret",
        password_hash="hash",
        created_at=datetime.now(),
    )
    assert user.password == "secret"
    assert user.password_hash == "hash"
    assert User.password_hash.name == "password_hash"
    assert user.model_dump()["password_hash"] == "hash"


def test_constructor_checks_names_and_required_fields(read: UserRead) -> None:
    read_type = type(read)
    with pytest.raises(
        TypeError, match="Missing DTO fields: created_at, email"
    ):
        read_type()
    with pytest.raises(AttributeError, match="Unknown DTO field 'typo'"):
        read_type(email="a", created_at=datetime.now(), typo=True)
    with pytest.raises(AttributeError, match="Unknown DTO field"):
        read.typo = 1
    # DTOs deliberately perform no boundary validation or value coercion.
    unvalidated = read_type(email=123, created_at="not a datetime")
    assert vars(unvalidated)["email"] == 123
    assert vars(unvalidated)["created_at"] == "not a datetime"


def test_no_forbidden_default_factory_is_executed() -> None:
    def forbidden_default() -> str:
        pytest.fail("An internal default must not execute while building a DTO")

    class WithDefaults(BaseSchema):
        name: Field[str] = Field(default="default")
        secret: InternalField[str] = InternalField(
            default_factory=forbidden_default
        )

    class Public(ReadDTO, WithDefaults): ...

    class ChildPublic(Public): ...

    assert Public().name == "default"
    assert ChildPublic().name == "default"


def test_optional_decorator_remains_compatible() -> None:
    @dto
    class Explicit(ReadDTO, User): ...

    read = Explicit(email="a", created_at=datetime.now())
    assert read.email == "a"
    assert (
        Explicit.__fastsprout_forbidden__ == UserRead.__fastsprout_forbidden__
    )
    assert dto(Explicit) is Explicit


def test_subclasses_preserve_methods_and_each_visibility_mode() -> None:
    @dto
    class Create(UserCreate): ...

    class Update(UserUpdate): ...

    child = GrandchildRead(email="a", created_at=datetime.now())
    assert child.display() == "a"
    create = Create(email="a", password="secret")
    update = Update(email="a", password="secret", created_at=datetime.now())
    assert create.password == update.password == "secret"
    assert isinstance(update.created_at, datetime)
    internal_name = "password_hash"
    for value in (create, update):
        assert type(value).__fastsprout_source__ is User
        for obj in (value, type(value)):
            with pytest.raises(AttributeError, match="not accessible"):
                getattr(obj, internal_name)
    read_name = "created_at"
    for obj in (create, Create):
        with pytest.raises(AttributeError, match="not accessible"):
            getattr(obj, read_name)


def test_malformed_declarations_fail_when_created() -> None:
    with pytest.raises(TypeError, match="Declare class"):
        type("MissingSource", (ReadDTO,), {})
    with pytest.raises(TypeError, match="Declare class"):
        type("MixedModes", (ReadDTO, WriteDTO, User), {})
    with pytest.raises(TypeError, match="Derive each DTO"):
        type("ChangedMode", (WriteDTO, UserRead), {})
    with pytest.raises(TypeError, match="require init=False"):
        type("GeneratedInit", (ReadDTO, User), {}, init=True)
    with pytest.raises(TypeError, match="Use a DTO class"):
        ReadDTO()


@pytest.mark.parametrize(
    "method",
    [
        "model_validate",
        "model_validate_json",
        "model_validate_strings",
        "model_construct",
    ],
)
def test_inherited_validation_cannot_return_an_unrestricted_source(
    method: str,
    read: UserRead,
) -> None:
    with pytest.raises(TypeError, match="DTOs use their constructor"):
        getattr(type(read), method)({"password_hash": "secret"})


def test_repr_and_runtime_guard_after_widening(read: UserRead) -> None:
    assert "email='a@b.c'" in repr(read)
    assert "password" not in repr(read)
    widened: Any = read
    with pytest.raises(AttributeError, match="not accessible"):
        _ = widened.password
