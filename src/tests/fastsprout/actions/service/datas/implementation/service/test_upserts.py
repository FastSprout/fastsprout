import pytest

from fastsprout.actions import DataS
from fastsprout.core import Chunk, Depends
from fastsprout.data import DataR, sql
from fastsprout.data.utils.iterable import resolve_any_iterable
from fastsprout.testing.core import given, then, when

from ...common import Record, RecordRead


class TestUpserts:
    async def test_insert_then_update_preserves_internal_fields(
        self, records: DataS[Record]
    ) -> None:
        # given
        service = DataS(Record, read=RecordRead)
        entity = Record(name="Batman", system_key="stored")
        # when
        created = await service.upsert(entity)
        updated = await service.upsert(
            Record(id=created.id, name="Bruce", system_key="overwritten")
        )
        # then
        assert isinstance(created, RecordRead)
        assert isinstance(updated, RecordRead)
        assert created.id == updated.id
        assert updated.name == "Bruce"
        stored = await records.get(created.id)
        assert stored is not None
        assert stored.system_key == "stored"
        assert await records.count() == 1

    @pytest.mark.parametrize("asynchronous", [False, True])
    async def test_bulk_mixes_insert_and_update_in_input_order(
        self, records: DataS[Record], asynchronous: bool
    ) -> None:
        # given
        existing = await records.create(
            Record(name="Batman", system_key="stored")
        )
        sizes: list[int] = []

        async def check(entities: Chunk[Record], operation: str) -> None:
            assert operation == "bulk_upsert"
            sizes.append(len([entity async for entity in entities]))

        service = DataS(
            Record, read=RecordRead, chunk_size=2, dependencies=[Depends(check)]
        )
        inputs = (
            entity
            for entity in (
                Record(name="Robin"),
                Record(id=existing.id, name="Bruce", system_key="changed"),
                Record(name="Batgirl"),
            )
        )
        # when
        stream = service.bulk_upsert(
            resolve_any_iterable(inputs) if asynchronous else inputs
        )
        assert sizes == []
        results = await stream.to_list()
        # then
        assert [row.name for row in results] == ["Robin", "Bruce", "Batgirl"]
        assert all(isinstance(row, RecordRead) for row in results)
        assert sizes == [2, 1]
        stored = await records.get(existing.id)
        assert stored is not None and stored.system_key == "stored"
        assert await records.count() == 3
        assert await service.bulk_upsert([]).to_list() == []

    @pytest.mark.parametrize("schema", ["create", "update", "read"])
    async def test_missing_schema_disables_upserts(
        self, records: DataS[Record], schema: str
    ) -> None:
        # given
        service = {
            "create": DataS(Record, create=None),
            "update": DataS(Record, update=None),
            "read": DataS(Record, read=None),
        }[schema]
        # then
        with pytest.raises(AttributeError, match="disabled"):
            await service.upsert(Record(name="Batman"))
        with pytest.raises(AttributeError, match="disabled"):
            await service.bulk_upsert([]).to_list()

    async def test_later_chunk_failure_rolls_back_the_operation(
        self, records: DataS[Record]
    ) -> None:
        # given
        async def reject(entities: Chunk[Record]) -> None:
            async for entity in entities:
                if entity.name == "rejected":
                    raise ValueError("Rejected")

        service = DataS(Record, chunk_size=1, dependencies=[Depends(reject)])
        # when
        with pytest.raises(ValueError, match="Rejected"):
            await service.bulk_upsert(
                Record(name=name) for name in ("first", "rejected")
            ).to_list()
        # then
        async with DataR() as datar:
            assert await records.count(datar=datar) == 0

    @given("a new record for an explicit upsert transaction")
    def new_entity(self) -> Record:
        return Record(name="Batman")

    @when("a transaction fails after an upsert or bulk upsert")
    async def explicit_rollback(
        self, records: DataS[Record], new_entity: Record, bulk: bool
    ) -> ValueError:
        try:
            async with DataR() as datar:
                if bulk:
                    await records.bulk_upsert(
                        [new_entity], datar=datar
                    ).to_list()
                else:
                    await records.upsert(new_entity, datar=datar)
                raise ValueError("Rejected")
        except ValueError as error:
            return error

    @pytest.mark.parametrize("bulk", [False, True])
    @then("the explicit transaction rolls back all inserted records")
    async def test_explicit_transaction_rolls_back_upsert(
        self, records: DataS[Record], explicit_rollback: ValueError
    ) -> None:
        assert str(explicit_rollback) == "Rejected"
        assert await records.find_all(sql.SQLQuery(Record)) == []
