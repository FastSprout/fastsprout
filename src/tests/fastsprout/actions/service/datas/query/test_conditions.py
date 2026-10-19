from dataclasses import replace
from functools import partial

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from fastsprout.actions import DataS
from fastsprout.data import DataR, SimpleAsyncEntityStream, sql
from fastsprout.data.backend.sql.streams import SQLEntityStream
from fastsprout.data.capabilities.query import (
    And,
    Eq,
    FieldPredicate,
    Gte,
    In,
    Ne,
    Or,
    where,
)
from fastsprout.data.capabilities.query.predicate import evaluate
from fastsprout.testing.core import when_then

from ..common import (
    FILTER_CASES,
    LimitedPage,
    Record,
    RecordRead,
    Status,
)


@when_then("default schemas use the entity")
async def test_default_schemas_use_the_entity(
    records: DataS[Record],
) -> None:
    assert records.read_schema is Record
    assert records.create_schema is Record
    assert records.update_schema is Record
    assert records.patch_schema is Record
    async with DataR() as datar:
        created = await records.create(
            records.create_schema(name="Batman"), datar=datar
        )
        assert created.score == 10
        assert type(created) is Record
        assert created.system_key == "system"
        assert (
            await records.count(
                sql.SQLQuery(Record).where(where(Record.name, "bat")),
                datar=datar,
            )
            == 1
        )


@when_then("list and count share conditions before pagination")
async def test_list_and_count_share_conditions_before_pagination(
    records: DataS[Record],
) -> None:
    async with DataR() as datar:
        for name, score in (("Batman", 20), ("Batgirl", 30), ("Robin", 40)):
            await records.create(Record(name=name, score=score), datar=datar)
        query = sql.SQLQuery(
            entity=Record,
            statement=select(Record)
            .where(Record.score.orm >= 20)
            .order_by(Record.score.orm.desc()),
        )
        predicate = where(Record.name, "BAT")
        page = await records.list(
            replace(query).where(predicate).offset(1).limit(1),
            datar=datar,
        )
        assert page.total == 2
        assert query.conditions == ()
        assert query.offset_value == 0
        assert [row.name for row in page.items] == ["Batman"]
        assert (page.offset, page.limit) == (1, 1)
        assert (
            await records.count(replace(query).where(predicate), datar=datar)
            == 2
        )
        assert (
            await records.list(sql.SQLQuery(Record).limit(0), datar=datar)
        ).items == []
        assert (
            await records.list(sql.SQLQuery(Record).offset(99), datar=datar)
        ).total == 3
        limited = DataS(Record, page=LimitedPage)
        default_page = await limited.list(datar=datar)
        assert isinstance(default_page, LimitedPage)
        assert (len(default_page.items), default_page.limit) == (1, 1)
        assert (
            len(
                (
                    await limited.list(
                        sql.SQLQuery(Record).limit(2), datar=datar
                    )
                ).items
            )
            == 2
        )
        assert (
            len(
                (
                    await limited.list(
                        sql.SQLQuery(Record).limit(None), datar=datar
                    )
                ).items
            )
            == 3
        )
        with pytest.raises(ValidationError, match="less than or equal to 1000"):
            await limited.list(sql.SQLQuery(Record).limit(1001), datar=datar)

        samples = await records.stream(query, datar=datar).to_list()
        for condition, expected in FILTER_CASES:
            predicate = where(Record.score, condition)
            stream = records.stream(
                replace(query).where(predicate), datar=datar
            )
            assert {row.score async for row in stream} == expected
            assert await records.stream(
                replace(query).where(predicate), datar=datar
            ).count() == len(expected)
            memory = SimpleAsyncEntityStream(samples).filter(predicate)
            assert {row.score async for row in memory} == expected

        for expression in (
            Or(where(Record.name, Eq("Batman")), where(Record.score, Gte(40))),
            Or(where(Record.name, Eq("Batman")), lambda row: row.score >= 40),
        ):
            selection = replace(query).where(expression).offset(1).limit(1)
            page = await records.list(selection, datar=datar)
            assert await records.count(selection, datar=datar) == 2
            assert (selection.offset_value, selection.limit_value) == (1, 1)
            assert [
                row.name
                async for row in datar.ability(Record).stream(selection)
            ] == ["Batman"]
            assert page.total == 2
            assert [row.name for row in page.items] == ["Batman"]
            memory = SimpleAsyncEntityStream(samples).filter(
                partial(evaluate, expression)
            )
            assert {row.name async for row in memory} == {"Batman", "Robin"}

        selection = (
            replace(query)
            .where(where(Record.score, Gte(30)))
            .where(where(Record.name, Eq("Batgirl")))
        )
        assert len(selection.conditions) == 2
        assert await datar.ability(Record).stream(selection).count() == 1
        assert str(selection.build()).count(" AND ") == 2
        native = sql.SQLQuery(Record, select(Record).limit(1)).limit(None)
        assert await datar.ability(Record).stream(native).count() == 3
        with pytest.raises(TypeError, match="through stream"):
            replace(query).where(lambda row: row.score > 0).build()

        ordered = sql.SQLQuery(Record).order_by(Record.score, reverse=True)
        first = await records.list(ordered.limit(1), datar=datar)
        assert [row.name for row in first.items] == ["Robin"]
        following = replace(ordered).after(first.items[0])
        second = await records.list(following, datar=datar)
        assert [row.name for row in second.items] == ["Batgirl"]
        assert following.orderings[-1][0] == "id"
        memory = (
            SimpleAsyncEntityStream(samples)
            .filter(partial(evaluate, And(*following.conditions)))
            .sort(lambda row: row.score, reverse=True)
            .take(1)
        )
        assert [row.name async for row in memory] == ["Batgirl"]

        stream = datar.stream(query).take(1)
        selected = stream.filter(where(Record.name, Eq("Batman")))
        assert await selected.count() == 0
        assert not isinstance(selected, SQLEntityStream)
        assert (
            await records.count(
                sql.SQLQuery(Record).where(where(Record.score, In([20, 40]))),
                datar=datar,
            )
            == 2
        )


@when_then("query excludes system and write only fields")
async def test_query_excludes_system_and_write_only_fields(
    records: DataS[Record],
) -> None:
    async with DataR() as datar:
        await records.create(
            Record(name="Batman", status=Status.ACTIVE), datar=datar
        )
        with pytest.raises(AttributeError, match="public field"):
            await records.count(
                sql.SQLQuery(Record).where(
                    where(Record.system_key, Eq("system"))
                ),
                datar=datar,
            )
        with pytest.raises(AttributeError, match="not accessible"):
            await DataS(Record, read=RecordRead).count(
                sql.SQLQuery(Record).where(
                    lambda row: row.system_key == "system"
                ),
                datar=datar,
            )
        for condition in (
            where(Record.password, Eq("initial")),
            FieldPredicate(Record, "unknown", Eq("value")),
        ):
            with pytest.raises(AttributeError, match="public field"):
                await records.count(
                    sql.SQLQuery(Record).where(condition), datar=datar
                )
        assert (
            await records.count(
                sql.SQLQuery(Record).where(where(Record.status, Status.ACTIVE)),
                datar=datar,
            )
            == 1
        )
        assert (
            await records.count(
                sql.SQLQuery(Record).where(
                    where(Record.status, Status.ARCHIVED)
                ),
                datar=datar,
            )
            == 0
        )
        with pytest.raises(AttributeError, match="public field"):
            await records.count(
                sql.SQLQuery(Record).where(
                    Or(
                        where(Record.name, Eq("Batman")),
                        where(Record.system_key, Eq("system")),
                    )
                ),
                datar=datar,
            )
        await records.create(Record(name="Straße"), datar=datar)
        samples = await records.stream(
            sql.SQLQuery(Record), datar=datar
        ).to_list()
        next(row for row in samples if row.name == "Straße").note = None
        for predicate, expected in (
            (where(Record.note, In([None, "kept"])), 2),
            (where(Record.note, Eq(None)), 1),
            (where(Record.note, Ne("kept")), 1),
            (where(Record.note, Ne(None)), 1),
            (where(Record.name, "STRASSE"), 1),
            (where(Record.name, Eq("Straße")), 1),
        ):
            assert (
                await records.count(
                    sql.SQLQuery(Record).where(predicate), datar=datar
                )
                == expected
            ), predicate
            memory = SimpleAsyncEntityStream(samples).filter(predicate)
            assert await memory.count() == expected
