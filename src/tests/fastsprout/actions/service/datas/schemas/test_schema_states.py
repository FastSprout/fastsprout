from operator import methodcaller
from uuid import uuid4

from fastsprout.actions import DataS
from fastsprout.actions.service.datas import DataSOperation
from fastsprout.core import Undefined
from fastsprout.testing.core import then, when

from ..common import Record, RecordCreate, RecordPatch, RecordRead, RecordUpdate


class ConfiguredRecords(
    DataS[Record, RecordRead, RecordCreate, RecordUpdate, RecordPatch]
):
    read_schema = RecordRead
    create_schema = RecordCreate
    update_schema = RecordUpdate
    patch_schema = RecordPatch


@when("Undefined is applied to default and inherited schema configurations")
async def configured_defaults(
    records: DataS[Record],
) -> tuple[DataS[Record], ConfiguredRecords, RecordRead]:
    service = DataS(Record, create=Undefined)
    configured = ConfiguredRecords(create=Undefined)
    created = await configured.create(RecordCreate(name="Batman"))
    return service, configured, created


@then("undefined uses defaults or inherited schemas")
def test_undefined_uses_defaults_or_inherited_schemas(
    configured_defaults: tuple[DataS[Record], ConfiguredRecords, RecordRead],
) -> None:
    service, configured, created = configured_defaults
    assert service.read_schema is Record
    assert service.create_schema is Record
    assert service.update_schema is Record
    assert service.patch_schema is Record
    assert configured.create_schema is RecordCreate
    assert configured.read_schema is RecordRead
    assert isinstance(created, RecordRead)


@when("a service creates a record with an explicit schema")
async def explicit_schema(
    records: DataS[Record],
) -> tuple[DataS[Record, Record, RecordCreate], Record]:
    service = DataS(Record, create=RecordCreate)
    created = await methodcaller("create", RecordCreate(name="Batman"))(service)
    return service, created


@then("explicit schema replaces the entity")
def test_explicit_schema_replaces_the_entity(
    explicit_schema: tuple[DataS[Record, Record, RecordCreate], Record],
) -> None:
    service, created = explicit_schema
    assert service.create_schema is RecordCreate
    assert created.name == "Batman"


@when("create is attempted before and after changing the operation switch")
async def disabled_create(
    records: DataS[Record],
) -> tuple[frozenset[DataSOperation], bool, list[AttributeError]]:
    service = DataS(
        Record, create=None, operations=frozenset({"create", "exists"})
    )
    operations = service.operations
    exists = await service.exists(uuid4())
    errors: list[AttributeError] = []
    choices: tuple[frozenset[DataSOperation], ...] = (
        operations,
        frozenset({"create", "exists"}),
    )
    for enabled in choices:
        service.operations = enabled
        try:
            await methodcaller("create", RecordCreate(name="Batman"))(service)
        except AttributeError as error:
            errors.append(error)
    return operations, exists, errors


@then("none disables create even when operations enable it")
async def test_none_disables_create_even_when_operations_enable_it(
    records: DataS[Record],
    disabled_create: tuple[
        frozenset[DataSOperation], bool, list[AttributeError]
    ],
) -> None:
    operations, exists, errors = disabled_create
    assert operations == frozenset({"exists"})
    assert exists is False
    assert len(errors) == 2
    assert all("disabled" in str(error) for error in errors)
    assert await records.count() == 0


@when("update and patch are switched off independently")
async def independent_writes(
    records: DataS[Record],
) -> tuple[list[AttributeError], Record, Record]:
    created = await records.create(Record(name="Batman"))
    errors: list[AttributeError] = []
    no_update = DataS(Record, update=None)
    try:
        await no_update.update(created.id, Record(name="Robin"))
    except AttributeError as error:
        errors.append(error)
    patched = await no_update.patch(created.id, Record(name="Robin"))
    no_patch = DataS(Record, patch=None)
    try:
        await no_patch.patch(created.id, Record(name="Batgirl"))
    except AttributeError as error:
        errors.append(error)
    updated = await no_patch.update(
        created.id, no_patch.update_schema(name="Batgirl")
    )
    return errors, patched, updated


@then("update and patch can be disabled independently")
def test_update_and_patch_can_be_disabled_independently(
    independent_writes: tuple[list[AttributeError], Record, Record],
) -> None:
    errors, patched, updated = independent_writes
    assert len(errors) == 2
    assert all("disabled" in str(error) for error in errors)
    assert patched.name == "Robin"
    assert updated.name == "Batgirl"


@when("DTO-returning operations are attempted without a read schema")
async def no_read_operations(
    records: DataS[Record],
) -> tuple[frozenset[DataSOperation], list[AttributeError], bool, int, int]:
    created = await records.create(Record(name="Batman"))
    service = DataS(Record, read=None)
    errors: list[AttributeError] = []
    try:
        await service.get(created.id)
    except AttributeError as error:
        errors.append(error)
    try:
        await service.create(Record(name="Robin"))
    except AttributeError as error:
        errors.append(error)
    existed = await service.exists(created.id)
    count = await service.count()
    deleted = await service.delete(created.id)
    return service.operations, errors, existed, count, deleted


@then("no read schema disables operations returning a dto")
def test_no_read_schema_disables_operations_returning_a_dto(
    no_read_operations: tuple[
        frozenset[DataSOperation], list[AttributeError], bool, int, int
    ],
) -> None:
    operations, errors, existed, count, deleted = no_read_operations
    assert operations == frozenset(
        {
            "exists",
            "count",
            "delete",
            "bulk_delete",
            "update_by_query",
            "delete_by_query",
        }
    )
    assert len(errors) == 2
    assert all("disabled" in str(error) for error in errors)
    assert existed is True
    assert count == 1
    assert deleted == 1
