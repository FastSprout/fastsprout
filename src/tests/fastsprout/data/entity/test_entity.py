from collections.abc import Callable
from io import StringIO
from pathlib import Path
from shutil import copyfile
from uuid import UUID, uuid4

import pytest

from fastsprout.core import ReadField, WriteDTO
from fastsprout.data.entity import Entitieable
from fastsprout.data.streams.implementation import SimpleAsyncEntityStream
from fastsprout.testing.core import given, then, when
from tests.type_checking import TypeChecker

from .common import (
    DataclassEntity,
    DataclassRead,
    DataclassWrite,
    FieldsEntity,
    FieldsRead,
    FieldsWrite,
    SchemaEntity,
    SchemaRead,
    SchemaWrite,
    TextEntity,
)


class TestEntity:
    def test_typing_contract(self, type_checker: TypeChecker) -> None:
        # given
        source = Path(__file__).with_name("entity_typing.py.txt")
        copyfile(
            source.with_name("common.py"), type_checker.directory / "models.py"
        )
        # then
        type_checker.check(source)

    @pytest.mark.parametrize(
        "factory",
        [
            lambda id, name: SchemaEntity(id=id, name=name),
            DataclassEntity,
            FieldsEntity,
            lambda id, name: SchemaRead(id=id, name=name),
            lambda id, name: DataclassRead(id=id, name=name),
            lambda id, name: FieldsRead(id=id, name=name),
        ],
        ids=[
            "schema",
            "dataclass",
            "fields",
            "schema-read",
            "dataclass-read",
            "fields-read",
        ],
    )
    async def test_factory_preserves_identity_in_stream(
        self, factory: Callable[[UUID, str], Entitieable[UUID, None]]
    ) -> None:
        # given
        identifier = uuid4()
        entity = factory(identifier, "item")
        # when
        identities = [
            item.id async for item in SimpleAsyncEntityStream([entity])
        ]
        # then
        assert isinstance(entity, Entitieable)
        assert identities == [identifier]

    @pytest.mark.parametrize(
        "entity_type", [SchemaEntity, DataclassEntity, FieldsEntity]
    )
    def test_identity_keeps_read_marker(
        self, entity_type: type[Entitieable[UUID, None]]
    ) -> None:
        # when
        descriptors = [
            vars(base)["id"]
            for base in entity_type.__mro__
            if "id" in vars(base)
        ]
        # then
        assert isinstance(descriptors[0], ReadField)

    @pytest.mark.parametrize(
        "create_type", [SchemaWrite, DataclassWrite, FieldsWrite]
    )
    def test_write_dto_rejects_identity(
        self, create_type: type[WriteDTO]
    ) -> None:
        # given
        created = create_type(name="item")
        # then
        with pytest.raises(AttributeError, match="not accessible"):
            created.__getattribute__("id")
        with pytest.raises(AttributeError, match="not accessible"):
            create_type(id=uuid4(), name="item")


class TestEntityResource:
    @given("an entity with a non-SQL resource factory")
    def entity(self) -> TextEntity:
        return TextEntity(id=uuid4(), name="text")

    @when("the entity factory creates its declared resource")
    def resource(self, entity: TextEntity) -> StringIO:
        return entity.signpost().factory()

    @then("the native resource retains its operations and the entity binding")
    def test_resource(self, entity: TextEntity, resource: StringIO) -> None:
        assert isinstance(resource, StringIO)
        assert entity.signpost() is TextEntity.__signpost__
        assert entity.model_dump() == {"id": entity.id, "name": "text"}
