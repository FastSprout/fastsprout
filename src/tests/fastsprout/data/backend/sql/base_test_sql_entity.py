from typing import Any, ClassVar
from uuid import UUID

import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlmodel import Session

from fastsprout.core import Field
from fastsprout.data.backend.sql import SQLEntity


class BaseTestSQLEntity[E: SQLEntity[UUID]]:
    _entity_type: type[E]
    _data: ClassVar[dict[str, Any]]
    _updated_data: ClassVar[dict[str, Any]]
    _field_types: ClassVar[dict[str, type[Field[Any, Any]]]]

    @pytest.fixture
    def entity(self) -> E:
        return self._entity_type(**self._data)

    def test_fields_preserve_descriptors_and_orm_references(self):
        # given
        entity_type = self._entity_type
        for name, field_type in self._field_types.items():
            # when
            descriptor = vars(entity_type)[name]
            reference = getattr(entity_type, name)
            # then
            assert type(descriptor) is field_type
            assert reference.entity_cls is entity_type
            assert isinstance(reference.orm, InstrumentedAttribute)
            assert reference.orm.key == name

    def test_id_default_factory(self, entity: E):
        # when
        other = self._entity_type(**self._data)
        # then
        assert isinstance(entity.id, UUID)
        assert entity.id != other.id

    def test_persistence(
        self, entity: E, sql_session_factory: sessionmaker[Session]
    ):
        # given
        identifier = entity.id
        expected = entity.model_dump()
        # when
        with sql_session_factory() as session:
            session.add(entity)
            session.commit()
        # then
        with sql_session_factory() as session:
            loaded = session.get(self._entity_type, identifier)
            assert loaded is not None
            assert loaded.model_dump() == expected
            # when
            for name, value in self._updated_data.items():
                setattr(loaded, name, value)
            session.commit()
        # then
        with sql_session_factory() as session:
            updated = session.get(self._entity_type, identifier)
            assert updated is not None
            assert updated.model_dump() == expected | self._updated_data
