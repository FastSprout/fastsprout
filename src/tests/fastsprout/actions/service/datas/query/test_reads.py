from dataclasses import replace

import pytest
from sqlalchemy.exc import MultipleResultsFound

from fastsprout.actions import DataS
from fastsprout.core import dataclass
from fastsprout.data import DataR, sql
from fastsprout.data.capabilities.query import Between, Eq, Not, NotIn, where
from fastsprout.testing.core import then, when

from ..common import Record


@dataclass(frozen=True)
class QueryChange:
    updated: int
    deleted: int


@when("three records with equal sort values are persisted")
async def tied_records(
    records: DataS[Record], active_datar: DataR
) -> DataS[Record]:
    for name in ("Batman", "Robin", "Batgirl"):
        await records.create(Record(name=name), datar=active_datar)
    return records


@when("records numbered from zero to two are persisted")
async def numbered_records(
    records: DataS[Record], active_datar: DataR
) -> DataS[Record]:
    for score in range(3):
        await records.create(
            Record(name=str(score), score=score), datar=active_datar
        )
    return records


@then("read modes and cursor ties")
async def test_read_modes_and_cursor_ties(
    tied_records: DataS[Record], active_datar: DataR
) -> None:
    records, datar = tied_records, active_datar
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


@then("negation and between match python")
async def test_negation_and_between_match_python(
    numbered_records: DataS[Record],
    active_datar: DataR,
) -> None:
    records, datar = numbered_records, active_datar
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


@when("a record is upserted twice and changed and deleted by query")
async def upsert_changes(
    records: DataS[Record], active_datar: DataR
) -> tuple[str, int, QueryChange, int]:
    datar = active_datar
    hero = await records.upsert(Record(name="Batman"), datar=datar)
    hero.name = "Robin"
    updated_name = (await records.upsert(hero, datar=datar)).name
    query = sql.SQLQuery(Record).where(where(Record.name, Eq("Robin")))
    updated = await records.update_by_query(
        query, Record.score.set(42), datar=datar
    )
    score = (await records.find_exactly_one(query, datar=datar)).score
    deleted = await records.delete_by_query(query, datar=datar)
    return (
        updated_name,
        score,
        QueryChange(updated, deleted),
        await records.count(datar=datar),
    )


@then("upsert and query mutations")
def test_upsert_and_query_mutations(
    upsert_changes: tuple[str, int, QueryChange, int],
) -> None:
    name, score, changes, remaining = upsert_changes
    assert name == "Robin"
    assert score == 42
    assert changes == QueryChange(updated=1, deleted=1)
    assert remaining == 0


@when("ordered and Python-predicate queries update and delete records")
async def ordered_changes(
    records: DataS[Record],
) -> tuple[QueryChange, Record | None, bool, QueryChange, list[Record]]:
    async with DataR() as datar:
        for score in (10, 20, 30):
            await records.create(
                Record(name=str(score), score=score), datar=datar
            )
        first = (
            sql.SQLQuery(Record).order_by(Record.score, reverse=True).limit(1)
        )
        first_updated = await records.update_by_query(
            first, Record.score.set(40), datar=datar
        )
        top = await records.get(first, datar=datar)
        first_deleted = await records.delete_by_query(first, datar=datar)
        fallback = sql.SQLQuery(Record).where(lambda row: row.score == 10)
        existed = await records.exists(fallback, datar=datar)
        fallback_updated = await records.update_by_query(
            fallback, Record.score.set(15), datar=datar
        )
        fallback_deleted = await records.delete_by_query(
            sql.SQLQuery(Record).where(lambda row: row.score == 15),
            datar=datar,
        )
        remaining = await records.find_all(sql.SQLQuery(Record), datar=datar)
    return (
        QueryChange(first_updated, first_deleted),
        top,
        existed,
        QueryChange(fallback_updated, fallback_deleted),
        remaining,
    )


@then("query writes preserve order limit and python predicates")
def test_query_writes_preserve_order_limit_and_python_predicates(
    ordered_changes: tuple[
        QueryChange, Record | None, bool, QueryChange, list[Record]
    ],
) -> None:
    first, top, existed, fallback, remaining = ordered_changes
    assert first == QueryChange(updated=1, deleted=1)
    assert top is not None and top.name == "30" and top.score == 40
    assert existed
    assert fallback == QueryChange(updated=1, deleted=1)
    assert [row.score for row in remaining] == [20]
