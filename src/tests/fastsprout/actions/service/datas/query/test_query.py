import pytest
from pydantic import ValidationError

from fastsprout.actions import DataS, Page
from fastsprout.data import DataR, sql
from fastsprout.data.capabilities.query import Eq, Gte, where
from fastsprout.testing.core import then, when

from ..common import (
    LimitedPage,
    Record,
    RecordCreate,
    RecordPatch,
    RecordRead,
    RecordUpdate,
    RecordWrite,
)


@when("a record is patched, cleared, and patched with an empty payload")
async def patch_results(
    records: DataS[Record],
) -> tuple[Record, Record, Record]:
    created = await records.create(
        Record(name="Batman", score=123, note="original")
    )
    patched = await records.patch(
        created.id, records.patch_schema(name="Robin")
    )
    cleared = await records.patch(created.id, records.patch_schema(note=None))
    unchanged = await records.patch(created.id, records.patch_schema())
    return patched, cleared, unchanged


@then("patch preserves omitted defaults and accepts explicit null")
async def test_patch_preserves_omitted_defaults_and_accepts_explicit_null(
    records: DataS[Record],
    patch_results: tuple[Record, Record, Record],
) -> None:
    patched, cleared, unchanged = patch_results
    assert (patched.name, patched.score, patched.note) == (
        "Robin",
        123,
        "original",
    )
    assert cleared.note is None
    assert cleared.score == 123
    assert (
        await records.count(
            sql.SQLQuery(Record).where(where(Record.note, Eq(None)))
        )
        == 1
    )
    assert unchanged.name == "Robin"


@when("incomplete and default write payloads are submitted")
async def update_result(
    records: DataS[Record],
) -> tuple[Record, TypeError | None, type[RecordWrite]]:
    created = await records.create(
        Record(name="Batman", score=123, note="original")
    )
    service = DataS(Record, update=RecordWrite, patch=RecordPatch)
    failure = None
    try:
        await service.update(created.id, Record(score=8))
    except TypeError as error:
        failure = error
    updated = await records.update(
        created.id, records.update_schema(name="Robin")
    )
    return updated, failure, service.update_schema


@then("update requires complete write payload and applies defaults")
def test_update_requires_complete_write_payload_and_applies_defaults(
    update_result: tuple[Record, TypeError | None, type[RecordWrite]],
) -> None:
    updated, failure, schema = update_result
    assert isinstance(failure, TypeError)
    assert "Missing DTO fields" in str(failure)
    assert updated.score == 10
    assert updated.note == "kept"
    with pytest.raises(AttributeError, match="not accessible"):
        schema(system_key="changed")
    with pytest.raises(AttributeError, match="not accessible"):
        schema(id=updated.id)


@when("custom create, patch, and update schemas are used")
async def custom_results(
    records: DataS[Record],
) -> tuple[RecordRead, RecordRead, RecordRead, list[RecordRead]]:
    service = DataS(
        Record,
        read=RecordRead,
        create=RecordCreate,
        update=RecordUpdate,
        patch=RecordPatch,
    )
    created = await service.create(RecordCreate(name="Batman"))
    patched = await service.patch(created.id, RecordPatch(name="Robin"))
    updated = await service.update(
        created.id, RecordUpdate(name="Batgirl", score=42)
    )
    page = await service.list()
    return created, patched, updated, page.items


@then("custom schemas preserve read type for every result")
def test_custom_schemas_preserve_read_type_for_every_result(
    custom_results: tuple[RecordRead, RecordRead, RecordRead, list[RecordRead]],
) -> None:
    created, patched, updated, items = custom_results
    assert isinstance(created, RecordRead)
    assert created.label() == "BATMAN"
    assert isinstance(patched, RecordRead)
    assert patched.score == 10
    assert patched.note == "kept"
    assert isinstance(updated, RecordRead)
    assert updated.note == "replacement default"
    assert isinstance(items[0], RecordRead)


class SelectedRecords(DataS[Record]): ...


@when("matching and non-matching records are created")
async def selected_records(
    records: DataS[Record], active_datar: DataR
) -> SelectedRecords:
    await records.create(Record(name="Batman", score=50), datar=active_datar)
    await records.create(Record(name="Robin", score=5), datar=active_datar)
    return SelectedRecords()


@then("query applies to list and count")
async def test_query_applies_to_list_and_count(
    selected_records: SelectedRecords,
    active_datar: DataR,
) -> None:
    query = sql.SQLQuery(Record).where(where(Record.score, Gte(20)))
    assert await selected_records.count(query, datar=active_datar) == 1
    assert [
        row.name
        for row in (
            await selected_records.list(query, datar=active_datar)
        ).items
    ] == ["Batman"]


@when("a page is created with its configured default limit")
def configured_page() -> LimitedPage[RecordCreate]:
    return LimitedPage[RecordCreate](
        items=[RecordCreate(name="Batman")], total=1
    )


@then("query checks entity and pagination")
async def test_query_checks_entity_and_pagination(
    configured_page: LimitedPage[RecordCreate],
) -> None:
    with pytest.raises(ValueError, match="limit must be non-negative"):
        sql.SQLQuery(Record).limit(-1)
    with pytest.raises(ValueError, match="offset must be non-negative"):
        sql.SQLQuery(Record).offset(-1)
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        Page[RecordCreate](items=[], total=-1)
    page = configured_page
    assert (
        LimitedPage[RecordCreate].model_validate_json(page.model_dump_json())
        == page
    )
    schema = LimitedPage[RecordCreate].model_json_schema()
    assert schema["properties"]["total"]["minimum"] == 0
    assert schema["properties"]["offset"]["minimum"] == 0
    assert schema["properties"]["limit"]["anyOf"][0]["maximum"] == 1000
