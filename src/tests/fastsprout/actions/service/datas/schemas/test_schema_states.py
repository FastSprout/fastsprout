from operator import methodcaller
from uuid import uuid4

import pytest

from fastsprout.actions import DataS
from fastsprout.core import Undefined
from fastsprout.testing.core import when_then

from ..common import (
    Record,
    RecordCreate,
    RecordPatch,
    RecordRead,
    RecordUpdate,
)


class ConfiguredRecords(
    DataS[
        Record,
        RecordRead,
        RecordCreate,
        RecordUpdate,
        RecordPatch,
    ]
):
    read_schema = RecordRead
    create_schema = RecordCreate
    update_schema = RecordUpdate
    patch_schema = RecordPatch


@when_then("undefined uses defaults or inherited schemas")
async def test_undefined_uses_defaults_or_inherited_schemas(
    records: DataS[Record],
) -> None:
    service = DataS(Record, create=Undefined)
    assert service.read_schema is Record
    assert service.create_schema is Record
    assert service.update_schema is Record
    assert service.patch_schema is Record
    configured = ConfiguredRecords(create=Undefined)
    assert configured.create_schema is RecordCreate
    assert configured.read_schema is RecordRead
    created = await configured.create(RecordCreate(name="Batman"))
    assert isinstance(created, RecordRead)


@when_then("explicit schema replaces the entity")
async def test_explicit_schema_replaces_the_entity(
    records: DataS[Record],
) -> None:
    service = DataS(Record, create=RecordCreate)
    assert service.create_schema is RecordCreate
    created = await methodcaller("create", RecordCreate(name="Batman"))(service)
    assert created.name == "Batman"


@when_then("none disables create even when operations enable it")
async def test_none_disables_create_even_when_operations_enable_it(
    records: DataS[Record],
) -> None:
    service = DataS(
        Record, create=None, operations=frozenset({"create", "exists"})
    )
    assert service.operations == frozenset({"exists"})
    assert await service.exists(uuid4()) is False
    with pytest.raises(AttributeError, match="disabled"):
        await methodcaller("create", RecordCreate(name="Batman"))(service)
    service.operations = frozenset({"create", "exists"})
    with pytest.raises(AttributeError, match="disabled"):
        await methodcaller("create", RecordCreate(name="Batman"))(service)
    assert await records.count() == 0


@when_then("update and patch can be disabled independently")
async def test_update_and_patch_can_be_disabled_independently(
    records: DataS[Record],
) -> None:
    created = await records.create(Record(name="Batman"))
    no_update = DataS(Record, update=None)
    with pytest.raises(AttributeError, match="disabled"):
        await no_update.update(created.id, Record(name="Robin"))
    patched = await no_update.patch(created.id, Record(name="Robin"))
    assert patched.name == "Robin"

    no_patch = DataS(Record, patch=None)
    with pytest.raises(AttributeError, match="disabled"):
        await no_patch.patch(created.id, Record(name="Batgirl"))
    updated = await no_patch.update(
        created.id, no_patch.update_schema(name="Batgirl")
    )
    assert updated.name == "Batgirl"


@when_then("no read schema disables operations returning a dto")
async def test_no_read_schema_disables_operations_returning_a_dto(
    records: DataS[Record],
) -> None:
    created = await records.create(Record(name="Batman"))
    service = DataS(Record, read=None)
    assert service.operations == frozenset(
        {
            "exists",
            "count",
            "delete",
            "bulk_delete",
            "update_by_query",
            "delete_by_query",
        }
    )
    with pytest.raises(AttributeError, match="disabled"):
        await service.get(created.id)
    with pytest.raises(AttributeError, match="disabled"):
        await service.create(Record(name="Robin"))
    assert await service.exists(created.id) is True
    assert await service.count() == 1
    assert await service.delete(created.id) == 1
