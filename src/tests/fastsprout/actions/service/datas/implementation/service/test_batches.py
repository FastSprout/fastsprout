from collections.abc import AsyncIterator
from uuid import uuid4

import pytest

from fastsprout.actions import DataS
from fastsprout.core import Chunk, Depends
from fastsprout.core.types import AnyIterable
from fastsprout.data import DataR

from ...common import (
    Record,
    RecordCreate,
    RecordPatch,
    RecordRead,
    RecordUpdate,
    RecordValidation,
)


async def async_items[T](values: list[T]) -> AsyncIterator[T]:
    for value in values:
        yield value


@pytest.mark.parametrize("source", ["list", "generator", "async_generator"])
async def test_batch_writes_accept_single_use_iterables_and_return_read_dtos(
    records: DataS[Record], source: str
) -> None:
    service = DataS(
        Record,
        read=RecordRead,
        create=RecordCreate,
        update=RecordUpdate,
        patch=RecordPatch,
    )

    def iterable[T](values: list[T]) -> AnyIterable[T]:
        if source == "generator":
            return (value for value in values)
        if source == "async_generator":
            return async_items(values)
        return values

    created = await service.bulk_create(
        iterable([RecordCreate(name="Batman"), RecordCreate(name="Robin")])
    ).to_list()
    assert [item.name for item in created] == ["Batman", "Robin"]
    with pytest.raises(AttributeError):
        created[0].__getattribute__("system_key")
    updated = await service.bulk_update(
        iterable(
            [
                (created[1].id, RecordUpdate(name="Dick", score=30)),
                (created[0].id, RecordUpdate(name="Bruce", score=20)),
            ]
        )
    ).to_list()
    assert [item.name for item in updated] == ["Dick", "Bruce"]
    patched = await service.bulk_patch(
        iterable(
            [(item.id, RecordPatch(note=None)) for item in reversed(updated)]
        )
    ).to_list()
    assert [item.id for item in patched] == [
        item.id for item in reversed(updated)
    ]
    assert [item.score for item in patched] == [20, 30]
    assert [item.note for item in patched] == [None, None]
    assert (
        await service.bulk_delete(iterable([item.id for item in patched])) == 2
    )
    assert await records.count() == 0


async def test_bulk_entity_update_and_empty_batches(
    records: DataS[Record],
):
    created = await records.bulk_create(
        Record(name=name) for name in ["a", "b"]
    ).to_list()
    updated = await records.bulk_update(
        async_items([item.model_copy(update={"score": 40}) for item in created])
    ).to_list()
    assert [item.score for item in updated] == [40, 40]
    assert await records.bulk_create([]).to_list() == []
    assert await records.bulk_update([]).to_list() == []
    assert await records.bulk_patch([]).to_list() == []
    assert await records.bulk_delete([]) == 0


async def test_chunk_validation_rejects_before_writing_that_chunk(
    records: DataS[Record],
) -> None:
    service = DataS(
        Record, chunk_size=2, dependencies=[Depends(RecordValidation())]
    )
    async with DataR() as datar:
        with pytest.raises(ValueError, match="non-negative"):
            await service.bulk_create(
                async_items([Record(name="a"), Record(name="b", score=-1)]),
                datar=datar,
            ).to_list()
        assert await records.count(datar=datar) == 0
        service.chunk_size = 1
        with pytest.raises(ValueError, match="non-negative"):
            await service.bulk_create(
                async_items([Record(name="a"), Record(name="b", score=-1)]),
                datar=datar,
            ).to_list()
        assert await records.count(datar=datar) == 1


@pytest.mark.parametrize("operation", ["bulk_update", "bulk_patch"])
async def test_missing_last_key_does_not_write_first_item(
    records: DataS[Record], operation: str
) -> None:
    created = await records.create(Record(name="Batman"))
    service = DataS(Record, update=RecordUpdate, patch=RecordPatch)
    async with DataR() as datar:
        with pytest.raises(LookupError):
            if operation == "bulk_update":
                await service.bulk_update(
                    [
                        (created.id, RecordUpdate(name="Bruce", score=20)),
                        (uuid4(), RecordUpdate(name="missing", score=20)),
                    ],
                    datar=datar,
                ).to_list()
            else:
                await service.bulk_patch(
                    [
                        (created.id, RecordPatch(name="Bruce")),
                        (uuid4(), RecordPatch(name="missing")),
                    ],
                    datar=datar,
                ).to_list()
        found = await records.get(created.id, datar=datar)
        assert found is not None
        assert found.name == "Batman"


async def test_batch_service_and_router_dependencies_share_the_context(
    records: DataS[Record],
) -> None:
    calls: list[str] = []
    produced: list[str] = []
    checked: list[list[str]] = []

    async def service_check(
        entities: Chunk[Record], operation: str, datar: DataR
    ) -> None:
        assert operation == "bulk_create"
        assert datar is data
        calls.append("service")
        checked.append([entity.name async for entity in entities])

    async def check_again(entities: Chunk[Record]) -> None:
        assert [entity.name async for entity in entities] == checked[-1]

    def router_check(operation: str, datar: DataR) -> None:
        assert datar is data
        calls.append(operation)

    def produce(name: str) -> Record:
        produced.append(name)
        return Record(name=name)

    service = DataS(
        Record,
        chunk_size=2,
        dependencies=[Depends(service_check), Depends(check_again)],
    )
    async with DataR(dependencies=[Depends(router_check)]) as data:
        stream = service.bulk_create(
            (produce(str(index)) for index in range(5)), datar=data
        )
        assert produced == []
        assert calls == []
        iterator = aiter(stream)
        created = [(await anext(iterator)).name]
        assert len(produced) == 2
        created.extend([item.name async for item in iterator])
        assert created == produced
    assert len(created) == 5
    assert list(map(len, checked)) == [2, 2, 1]
    assert calls == ["service", "bulk_create"] * 3


@pytest.mark.parametrize(
    "operation", ["bulk_create", "bulk_update", "bulk_patch"]
)
async def test_none_schema_disables_corresponding_batch(
    records: DataS[Record], operation: str
) -> None:
    service = DataS(Record, create=None, update=None, patch=None)
    with pytest.raises(AttributeError, match="disabled"):
        if operation == "bulk_create":
            await service.bulk_create([]).to_list()
        elif operation == "bulk_update":
            await service.bulk_update([]).to_list()
        else:
            await service.bulk_patch([]).to_list()


async def test_batch_failure_rolls_back_service_dependency_side_effects(
    records: DataS[Record],
) -> None:
    async def related(datar: DataR) -> None:
        await records.create(Record(name="Related"), datar=datar)

    service = DataS(Record, dependencies=[Depends(related)])
    with pytest.raises(ValueError, match="non-negative"):
        async with DataR(dependencies=[Depends(RecordValidation())]) as datar:
            await service.bulk_create(
                [Record(name="a"), Record(name="b", score=-1)], datar=datar
            ).to_list()
    async with DataR() as datar:
        assert await records.count(datar=datar) == 0


async def test_dependencies_replace_each_chunk_before_backend_write(
    records: DataS[Record],
) -> None:
    sizes: list[int] = []
    seen: list[str] = []

    async def select(entities: Chunk[Record]) -> Chunk[Record]:
        sizes.append(len([entity async for entity in entities]))
        return Chunk(entity async for entity in entities if entity.score > 0)

    async def rename(entities: Chunk[Record]) -> Chunk[Record]:
        return Chunk(
            Record(name=entity.name.upper(), score=entity.score)
            async for entity in entities
        )

    async def check(entities: Chunk[Record]) -> Chunk[Record]:
        values = [entity async for entity in entities]
        seen.extend(entity.name for entity in values)
        return Chunk(async_items(values))

    service = DataS(
        Record,
        chunk_size=2,
        dependencies=[Depends(select), Depends(rename), Depends(check)],
    )
    async with DataR() as datar:
        created = await service.bulk_create(
            async_items(
                [
                    Record(name="a", score=1),
                    Record(name="skip", score=0),
                    Record(name="b", score=2),
                ]
            ),
            datar=datar,
        ).to_list()
        assert [entity.name for entity in created] == ["A", "B"]
        assert await records.count(datar=datar) == 2
    assert sizes == [2, 1]
    assert seen == ["A", "B"]
