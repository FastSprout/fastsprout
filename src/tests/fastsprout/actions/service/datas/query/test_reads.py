from dataclasses import replace

import pytest
from sqlalchemy.exc import MultipleResultsFound

from fastsprout.actions import DataS
from fastsprout.data import DataR, sql
from fastsprout.data.capabilities.query import Between, Eq, Not, NotIn, where
from fastsprout.testing.core import when_then

from ..common import Record


@when_then("read modes and cursor ties")
async def test_read_modes_and_cursor_ties(records: DataS[Record]) -> None:
    async with DataR() as datar:
        for name in ("Batman", "Robin", "Batgirl"):
            await records.create(Record(name=name), datar=datar)
        query = sql.SQLQuery(Record).order_by(Record.score).limit(1)
        visited = []
        while (page := await records.list(query, datar=datar)).items:
            visited.append(page.items[0].id)
            query = replace(query, conditions=()).after(page.items[0])
        assert len(set(visited)) == len(visited) == 3
        selection = sql.SQLQuery(Record).where(where(Record.name, Eq("Robin")))
        assert (
            await records.find_exactly_one(selection, datar=datar)
        ).name == "Robin"
        assert (
            await records.find_exactly_one(
                Record.name.eq("Robin"), Record.score.gte(0), datar=datar
            )
        ).name == "Robin"
        first = await records.find_first(selection, datar=datar)
        assert first is not None and first.name == "Robin"
        assert len(await records.find_all(selection, datar=datar)) == 1
        with pytest.raises(MultipleResultsFound, match="exactly one"):
            await records.find_exactly_one(sql.SQLQuery(Record), datar=datar)
        assert (
            len(
                [
                    row
                    async for row in records.stream(
                        sql.SQLQuery(Record), datar=datar
                    )
                ]
            )
            == 3
        )
        chunks = [
            chunk
            async for chunk in records.stream(
                sql.SQLQuery(Record), datar=datar
            ).chunked(2)
        ]
        assert [len(chunk) for chunk in chunks] == [2, 1]


@when_then("negation and between match python")
async def test_negation_and_between_match_python(
    records: DataS[Record],
) -> None:
    async with DataR() as datar:
        for score in range(3):
            await records.create(
                Record(name=str(score), score=score), datar=datar
            )
        for condition, expected in (
            (Between(0, 1), {0, 1}),
            (NotIn([1]), {0, 2}),
            (Not(Between(0, 1)), {2}),
        ):
            predicate = where(Record.score, condition)
            found = await records.find_all(
                sql.SQLQuery(Record).where(predicate), datar=datar
            )
            assert {row.score for row in found} == expected
            assert {
                score
                for score in range(3)
                if await predicate(Record(name=str(score), score=score))
            } == expected


@when_then("upsert and query mutations")
async def test_upsert_and_query_mutations(records: DataS[Record]) -> None:
    async with DataR() as datar:
        hero = await records.upsert(Record(name="Batman"), datar=datar)
        hero.name = "Robin"
        assert (await records.upsert(hero, datar=datar)).name == "Robin"
        query = sql.SQLQuery(Record).where(where(Record.name, Eq("Robin")))
        assert (
            await records.update_by_query(
                query, Record.score.set(42), datar=datar
            )
            == 1
        )
        assert (await records.find_exactly_one(query, datar=datar)).score == 42
        assert await records.delete_by_query(query, datar=datar) == 1
        assert await records.count(datar=datar) == 0


@when_then("query writes preserve order limit and python predicates")
async def test_query_writes_preserve_order_limit_and_python_predicates(
    records: DataS[Record],
) -> None:
    async with DataR() as datar:
        for score in (10, 20, 30):
            await records.create(
                Record(name=str(score), score=score), datar=datar
            )
        first = (
            sql.SQLQuery(Record).order_by(Record.score, reverse=True).limit(1)
        )
        assert (
            await records.update_by_query(
                first, Record.score.set(40), datar=datar
            )
            == 1
        )
        top = await records.get(first, datar=datar)
        assert top is not None and top.name == "30" and top.score == 40
        assert await records.delete_by_query(first, datar=datar) == 1
        fallback = sql.SQLQuery(Record).where(lambda row: row.score == 10)
        assert await records.exists(fallback, datar=datar)
        assert (
            await records.update_by_query(
                fallback, Record.score.set(15), datar=datar
            )
            == 1
        )
        assert (
            await records.delete_by_query(
                sql.SQLQuery(Record).where(lambda row: row.score == 15),
                datar=datar,
            )
            == 1
        )
        assert [
            row.score
            for row in await records.find_all(sql.SQLQuery(Record), datar=datar)
        ] == [20]
