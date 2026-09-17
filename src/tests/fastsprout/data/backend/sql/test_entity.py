import subprocess
import sys
from uuid import UUID, uuid4

from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlmodel import Field as SQLField
from sqlmodel import Session, create_engine

from fastsprout.core import Field
from fastsprout.data.backend.sql import SQLEntity


class SearchField[T](Field[T]): ...


class SortField[T](Field[T]): ...


class CustomSQLBase(SQLEntity[UUID], table=False):
    id: Field[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    code: SearchField[str]
    inherited: SearchField[str]


class CustomSQLMiddle(CustomSQLBase, table=False):
    sort_key: SortField[str]


class CustomSQLRecord(CustomSQLMiddle):
    name: SearchField[str]


def test_sql_can_be_imported_in_a_fresh_interpreter() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from fastsprout.data.backend.sql import SQLEntity",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_sql_preserves_local_and_inherited_field_subclasses() -> None:
    assert type(vars(CustomSQLBase)["code"]) is SearchField
    assert type(vars(CustomSQLMiddle)["sort_key"]) is SortField
    assert type(vars(CustomSQLRecord)["code"]) is SearchField
    assert type(vars(CustomSQLRecord)["sort_key"]) is SortField
    assert type(vars(CustomSQLRecord)["inherited"]) is SearchField
    assert type(vars(CustomSQLRecord)["name"]) is SearchField
    for name in ("id", "code", "sort_key", "inherited", "name"):
        reference = getattr(CustomSQLRecord, name)
        assert reference.entity_cls is CustomSQLRecord
        assert isinstance(reference.orm, InstrumentedAttribute)
        assert reference.orm.key == name


def test_custom_sql_fields_preserve_defaults_and_persistence() -> None:
    record = CustomSQLRecord(
        code="a", sort_key="01", inherited="base", name="first"
    )
    identifier = record.id
    assert isinstance(identifier, UUID)
    engine = create_engine("sqlite://")
    CustomSQLRecord.__table__.create(engine)
    try:
        with Session(engine) as session:
            session.add(record)
            session.commit()
        with Session(engine) as session:
            loaded = session.get(CustomSQLRecord, identifier)
            assert loaded is not None
            assert loaded.code == "a"
            assert loaded.sort_key == "01"
            assert loaded.inherited == "base"
            assert loaded.name == "first"
            loaded.code = "updated"
            session.commit()
        with Session(engine) as session:
            updated = session.get(CustomSQLRecord, identifier)
            assert updated is not None
            assert updated.code == "updated"
    finally:
        engine.dispose()
