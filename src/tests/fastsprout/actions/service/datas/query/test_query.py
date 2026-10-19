import pytest
from pydantic import ValidationError

from fastsprout.actions import DataS, Page
from fastsprout.data import DataR, sql
from fastsprout.data.capabilities.query import Eq, Gte, where
from fastsprout.testing.core import when_then

from ..common import (
    LimitedPage,
    Record,
    RecordCreate,
    RecordPatch,
    RecordRead,
    RecordUpdate,
    RecordWrite,
)


@when_then("patch preserves omitted defaults and accepts explicit null")
async def test_patch_preserves_omitted_defaults_and_accepts_explicit_null(
    records: DataS[Record],
) -> None:
    created = await records.create(
        Record(name="Batman", score=123, note="original")
    )
    patched = await records.patch(
        created.id, records.patch_schema(name="Robin")
    )
    assert (patched.name, patched.score, patched.note) == (
        "Robin",
        123,
        "original",
    )
    cleared = await records.patch(created.id, records.patch_schema(note=None))
    assert cleared.note is None
    assert cleared.score == 123
    assert (
        await records.count(
            sql.SQLQuery(Record).where(where(Record.note, Eq(None)))
        )
        == 1
    )
    unchanged = await records.patch(created.id, records.patch_schema())
    assert unchanged.name == "Robin"


@when_then("update requires complete write payload and applies defaults")
async def test_update_requires_complete_write_payload_and_applies_defaults(
    records: DataS[Record],
) -> None:
    created = await records.create(
        Record(name="Batman", score=123, note="original")
    )
    service = DataS(Record, update=RecordWrite, patch=RecordPatch)
    with pytest.raises(TypeError, match="Missing DTO fields"):
        await service.update(created.id, Record(score=8))
    updated = await records.update(
        created.id, records.update_schema(name="Robin")
    )
    assert updated.score == 10
    assert updated.note == "kept"
    with pytest.raises(AttributeError, match="not accessible"):
        service.update_schema(system_key="changed")
    with pytest.raises(AttributeError, match="not accessible"):
        service.update_schema(id=created.id)


@when_then("custom schemas preserve read type for every result")
async def test_custom_schemas_preserve_read_type_for_every_result(
    records: DataS[Record],
) -> None:
    service = DataS(
        Record,
        read=RecordRead,
        create=RecordCreate,
        update=RecordUpdate,
        patch=RecordPatch,
    )
    created = await service.create(RecordCreate(name="Batman"))
    assert isinstance(created, RecordRead)
    assert created.label() == "BATMAN"
    patched = await service.patch(created.id, RecordPatch(name="Robin"))
    assert isinstance(patched, RecordRead)
    assert patched.score == 10
    assert patched.note == "kept"
    updated = await service.update(
        created.id, RecordUpdate(name="Batgirl", score=42)
    )
    assert isinstance(updated, RecordRead)
    assert updated.note == "replacement default"
    page = await service.list()
    assert isinstance(page.items[0], RecordRead)


class SelectedRecords(DataS[Record]): ...


@when_then("query applies to list and count")
async def test_query_applies_to_list_and_count(
    records: DataS[Record],
) -> None:
    async with DataR() as datar:
        await records.create(Record(name="Batman", score=50), datar=datar)
        await records.create(Record(name="Robin", score=5), datar=datar)
        service = SelectedRecords()
        query = sql.SQLQuery(Record).where(where(Record.score, Gte(20)))
        assert await service.count(query, datar=datar) == 1
        assert [
            row.name for row in (await service.list(query, datar=datar)).items
        ] == ["Batman"]


@when_then("query checks entity and pagination")
async def test_query_checks_entity_and_pagination(
    records: DataS[Record],
) -> None:
    with pytest.raises(ValueError, match="limit must be non-negative"):
        sql.SQLQuery(Record).limit(-1)
    with pytest.raises(ValueError, match="offset must be non-negative"):
        sql.SQLQuery(Record).offset(-1)
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        Page[RecordCreate](items=[], total=-1)
    page = LimitedPage[RecordCreate](
        items=[RecordCreate(name="Batman")], total=1
    )
    assert (
        LimitedPage[RecordCreate].model_validate_json(page.model_dump_json())
        == page
    )
    schema = LimitedPage[RecordCreate].model_json_schema()
    assert schema["properties"]["total"]["minimum"] == 0
    assert schema["properties"]["offset"]["minimum"] == 0
    assert schema["properties"]["limit"]["anyOf"][0]["maximum"] == 1000
