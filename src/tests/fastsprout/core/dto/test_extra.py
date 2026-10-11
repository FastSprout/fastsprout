from pathlib import Path

import pytest
from sqlmodel import Field as SQLField

from fastsprout.core import (
    BaseSchema,
    ExtraReadDTO,
    ExtraReadField,
    ExtraReadWriteDTO,
    ExtraWriteDTO,
    ExtraWriteField,
    Field,
    InternalField,
    ReadDTO,
    ReadField,
    ReadWriteDTO,
    WriteDTO,
    WriteField,
)
from fastsprout.core.dto import derive_dto
from fastsprout.core.dto.base import DTO
from fastsprout.data.backend.sql import SQLEntity
from tests.type_checking import TypeChecker


class Source(BaseSchema):
    name: Field[str] = Field(default="name")
    read: ReadField[str] = ReadField(default="read")
    write: WriteField[str] = WriteField(default="write")
    extra_read: ExtraReadField[str] = ExtraReadField(default="extra_read")
    extra_write: ExtraWriteField[str] = ExtraWriteField(default="extra_write")
    internal: InternalField[str] = InternalField(default="internal")


@pytest.mark.parametrize(
    ("mode", "allowed"),
    [
        (ReadDTO, {"name", "read"}),
        (WriteDTO, {"name", "write"}),
        (ReadWriteDTO, {"name", "read", "write"}),
        (ExtraReadDTO, {"name", "read", "extra_read"}),
        (ExtraWriteDTO, {"name", "write", "extra_write"}),
        (
            ExtraReadWriteDTO,
            {"name", "read", "write", "extra_read", "extra_write"},
        ),
    ],
)
def test_visibility(mode: type[DTO], allowed: set[str]) -> None:
    model = derive_dto(Source, mode)
    instance = model()
    assert derive_dto(Source, mode) is model
    assert set(vars(instance)) == allowed
    for name in allowed:
        assert getattr(instance, name) == name
        assert getattr(model, name).name == name
    for name in Source.model_fields.keys() - allowed:
        with pytest.raises(AttributeError, match="not accessible"):
            getattr(instance, name)
        with pytest.raises(AttributeError, match="not accessible"):
            getattr(model, name)
        with pytest.raises(AttributeError, match="not accessible"):
            setattr(instance, name, "changed")
        with pytest.raises(AttributeError, match="not accessible"):
            delattr(instance, name)
        with pytest.raises(AttributeError, match="not accessible"):
            model(**{name: "changed"})


def test_explicit_classes_and_inheritance() -> None:
    class ExtendedRead(ExtraReadDTO, Source): ...

    class Child(ExtendedRead): ...

    class ExtendedWrite(ExtraWriteDTO, Source): ...

    class ExtendedBoth(ExtraReadWriteDTO, Source): ...

    read = Child()
    read.extra_read = "changed"
    assert read.extra_read == "changed"
    assert ExtendedWrite().extra_write == "extra_write"
    assert ExtendedBoth().extra_read == "extra_read"
    assert ExtendedBoth().extra_write == "extra_write"
    assert Child.__fastsprout_source__ is Source
    assert Child.__fastsprout_operations__ == {"read", "extra_read"}
    assert Source().extra_read == "extra_read"
    assert Source().extra_write == "extra_write"


def test_hidden_extra_default_is_not_evaluated() -> None:
    def expensive_default() -> str:
        pytest.fail("Ordinary DTOs must not evaluate extra field defaults")

    class Expensive(BaseSchema):
        details: ExtraReadField[str] = ExtraReadField(
            default_factory=expensive_default
        )

    class Read(ReadDTO, Expensive): ...

    assert vars(Read()) == {}


def test_sql_extra_fields() -> None:
    class SQLSource(SQLEntity[int]):
        id: ReadField[int] = SQLField(primary_key=True)
        details: ExtraReadField[str]
        override: ExtraWriteField[int]

    class Read(ExtraReadDTO, SQLSource): ...

    class Write(ExtraWriteDTO, SQLSource): ...

    assert Read(id=1, details="details").details == "details"
    assert Write(override=2).override == 2
    assert Read.details.orm is SQLSource.details.orm
    with pytest.raises(AttributeError, match="not accessible"):
        Read(id=1, details="details", override=2)


def test_extra_typing(type_checker: TypeChecker) -> None:
    type_checker.check(Path(__file__).with_name("extra_typing.py.txt"))
