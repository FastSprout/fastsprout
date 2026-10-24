from datetime import datetime
from typing import ClassVar
from uuid import UUID

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlmodel import Session

from fastsprout.core import Field, InternalField, ReadField, WriteField
from fastsprout.data.backend.sql import SQLEntity
from fastsprout.testing.core import given, then, when

type SQLTestField = (
    Field[str]
    | ReadField[UUID]
    | ReadField[datetime]
    | WriteField[str]
    | InternalField[str]
    | InternalField[datetime | None]
)


class BaseTestSQLEntity[E: SQLEntity[UUID]]:
    entity_type: type[E]
    data: ClassVar[dict[str, str | datetime]]
    updated_data: ClassVar[dict[str, str]]
    field_types: ClassVar[dict[str, type[SQLTestField]]]

    @given("an entity with custom field values")
    def entity(self) -> E:
        return self.entity_type(**self.data)

    @when("the mapped descriptors and their class references are inspected")
    def field_checks(self) -> dict[str, tuple[bool, bool, bool]]:
        entity_type = self.entity_type
        checks: dict[str, tuple[bool, bool, bool]] = {}
        for name, field_type in self.field_types.items():
            descriptor = vars(entity_type)[name]
            reference = getattr(entity_type, name)
            checks[name] = (
                type(descriptor) is field_type,
                reference.entity_cls is entity_type,
                isinstance(reference.orm, InstrumentedAttribute)
                and reference.orm.key == name,
            )
        return checks

    @then("mapped fields preserve descriptor types, owners and ORM keys")
    def test_fields_preserve_descriptors_and_orm_references(
        self, field_checks: dict[str, tuple[bool, bool, bool]]
    ) -> None:
        assert field_checks == {
            name: (True, True, True) for name in self.field_types
        }

    @when("another entity is constructed without an explicit identity")
    def other(self) -> E:
        return self.entity_type(**self.data)

    @then("default factories produce distinct UUID identities")
    def test_id_default_factory(self, entity: E, other: E) -> None:
        assert isinstance(entity.id, UUID)
        assert entity.id != other.id

    @when("the entity is committed and loaded from a new session")
    def persisted(
        self, entity: E, sql_session_factory: sessionmaker[Session]
    ) -> tuple[E, E | None]:
        identifier = entity.id
        expected = entity.model_copy(deep=True)
        with sql_session_factory() as session:
            session.add(entity)
            session.commit()
        with sql_session_factory() as session:
            return expected, session.get(self.entity_type, identifier)

    @then("the stored entity preserves every custom field value")
    def test_persistence(self, persisted: tuple[E, E | None]) -> None:
        expected, loaded = persisted
        assert loaded is not None
        assert loaded.model_dump() == expected.model_dump()

    @when("the stored entity is updated and committed again")
    def updated(
        self,
        persisted: tuple[E, E | None],
        sql_session_factory: sessionmaker[Session],
    ) -> tuple[E, E | None]:
        expected, loaded = persisted
        if loaded is None:
            return expected, None
        expected = loaded.model_copy(update=self.updated_data)
        identifier = loaded.id
        with sql_session_factory() as session:
            session.add(loaded)
            for name, value in self.updated_data.items():
                setattr(loaded, name, value)
            session.commit()
        with sql_session_factory() as session:
            return expected, session.get(self.entity_type, identifier)

    @then("updated values survive loading in a new session")
    def test_updated_persistence(self, updated: tuple[E, E | None]) -> None:
        expected, loaded = updated
        assert loaded is not None
        assert loaded.model_dump() == expected.model_dump()
