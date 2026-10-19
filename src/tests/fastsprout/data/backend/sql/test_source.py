from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field as SQLField

from fastsprout.core import Field, ReadField
from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLEntity, SQLQuery, SQLSignpost
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY
from fastsprout.testing.core import given, when_then


class CRM(SQLSignpost): ...


class ERP(SQLSignpost): ...


class CRMModel(SQLEntity[int, CRM], table=False):
    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str]


class TestSQLSource:
    @given("a CRM source sharing the prepared SQL session")
    def crm(self, sql_signpost: SQLSignpost) -> CRM:
        return CRM(sql_signpost.factory)

    @pytest.mark.parametrize("source_type", [CRM, ERP, SQLSignpost])
    @when_then("source binding validates before replacing class metadata")
    def test_bind(self, crm: CRM, source_type: type[SQLSignpost]) -> None:
        class Bound(CRMModel, table=False):
            __signpost__ = crm

        candidate = source_type(crm.factory)
        if isinstance(candidate, CRM):
            candidate.bind(Bound)
            assert Bound.__signpost__ is candidate
        else:
            with pytest.raises(
                TypeError, match="__signpost__ must be an instance of CRM"
            ):
                candidate.bind(Bound)
            assert Bound.__signpost__ is crm

    @when_then(
        "a scoped entity keeps its source through inherited query execution"
    )
    async def test_inherited_source(
        self,
        crm: CRM,
        sql_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        class ScopedHero(CRMModel): ...

        crm.bind(ScopedHero)

        await sql_session.run_sync(
            lambda session: ScopedHero.__table__.create(session.connection())
        )
        async with DataR() as datar:
            ability = datar.ability(ScopedHero)
            await ability.create(ScopedHero(id=1, name="Batman"))
            query = ability.query_for().where(ScopedHero.name.eq("Batman"))
            found = await ability.find_first(query)
            assert found is not None
            assert (found.id, found.name) == (1, "Batman")
            assert query.entity is ScopedHero
            assert ScopedHero.__signpost__ is crm
            scoped_rows = await datar.stream(
                SQLQuery(ScopedHero, source=crm)
            ).to_list()
            assert [row.id for row in scoped_rows] == [1]

        pinned = SQLQuery(ScopedHero, source=crm)
        assert pinned.build().column_descriptions[0]["entity"] is ScopedHero
        monkeypatch.setattr(ScopedHero, "__signpost__", CRM(crm.factory))
        assert query.build().column_descriptions[0]["entity"] is ScopedHero
        with pytest.raises(TypeError, match="their declared signpost"):
            pinned.build()
        monkeypatch.setattr(ScopedHero, "__signpost__", ERP(crm.factory))
        with pytest.raises(
            TypeError, match="__signpost__ must be an instance of CRM"
        ):
            query.build()

    @when_then(
        "direct source declarations retain the existing query constructor"
    )
    def test_direct_source(self, crm: CRM) -> None:
        class DirectScoped(SQLEntity[int, CRM], table=False):
            __signpost__ = crm

        class AnyScoped(SQLEntity[int, Any], table=False):
            __signpost__ = crm

        for entity in (DirectScoped, AnyScoped):
            assert entity.__signpost__ is crm
            assert SQLQuery(entity).entity is entity

    @when_then("a mismatched source is rejected before SQL mapping")
    def test_wrong_source(self, crm: CRM) -> None:
        source = ERP(crm.factory)
        tables = tuple(SQL_ENTITY_REGISTRY.metadata.tables)
        with pytest.raises(
            TypeError, match="__signpost__ must be an instance of CRM"
        ):

            class InvalidScoped(CRMModel):
                __signpost__ = source

        with pytest.raises(
            TypeError, match="__signpost__ must be an instance of CRM"
        ):

            class InvalidDirect(SQLEntity[int, CRM]):
                __signpost__ = source

        assert tuple(SQL_ENTITY_REGISTRY.metadata.tables) == tables
