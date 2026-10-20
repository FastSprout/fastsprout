from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field as SQLField

from fastsprout.core import Field, ReadField
from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLEntity, SQLQuery, SQLSignpost
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY, SQLSource
from fastsprout.testing.core import given, then, when


class CRM(SQLSignpost): ...


class ERP(SQLSignpost): ...


class CRMModel(SQLEntity[int, CRM], table=False):
    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str]


class TestSQLSource:
    @given("a CRM source sharing the prepared SQL session")
    def crm(self, sql_signpost: SQLSignpost) -> CRM:
        return CRM(sql_signpost.factory)

    @when("a candidate signpost binds an entity scoped to CRM")
    def bound_candidate(
        self, crm: CRM, source_type: type[SQLSignpost]
    ) -> tuple[SQLSignpost, SQLSource, TypeError | None]:
        class Bound(CRMModel, table=False):
            __signpost__ = crm

        candidate = source_type(crm.factory)
        failure = None
        try:
            candidate.bind(Bound)
        except TypeError as error:
            failure = error
        return candidate, Bound.__signpost__, failure

    @pytest.mark.parametrize("source_type", [CRM, ERP, SQLSignpost])
    @then("source binding validates before replacing class metadata")
    def test_bind(
        self,
        crm: CRM,
        bound_candidate: tuple[SQLSignpost, SQLSource, TypeError | None],
    ) -> None:
        candidate, bound, failure = bound_candidate
        if isinstance(candidate, CRM):
            assert failure is None
            assert bound is candidate
        else:
            assert isinstance(failure, TypeError)
            assert "__signpost__ must be an instance of CRM" in str(failure)
            assert bound is crm

    @when("a scoped subclass is mapped and persisted through its bound source")
    async def inherited_entity(
        self, crm: CRM, sql_session: AsyncSession
    ) -> type[CRMModel]:
        class ScopedHero(CRMModel): ...

        crm.bind(ScopedHero)
        await sql_session.run_sync(
            lambda session: ScopedHero.__table__.create(session.connection())
        )
        async with DataR() as datar:
            await datar.ability(ScopedHero).create(
                ScopedHero(id=1, name="Batman")
            )
        return ScopedHero

    @then("a scoped entity keeps its source through inherited query execution")
    async def test_inherited_source(
        self,
        crm: CRM,
        inherited_entity: type[CRMModel],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        entity = inherited_entity
        async with DataR() as datar:
            ability = datar.ability(entity)
            query = ability.query_for().where(entity.name.eq("Batman"))
            found = await ability.find_first(query)
            assert found is not None
            assert (found.id, found.name) == (1, "Batman")
            assert query.entity is entity
            assert entity.__signpost__ is crm
            scoped_rows = await datar.stream(
                SQLQuery(entity, source=crm)
            ).to_list()
            assert [row.id for row in scoped_rows] == [1]

        pinned = SQLQuery(entity, source=crm)
        assert pinned.build().column_descriptions[0]["entity"] is entity
        monkeypatch.setattr(entity, "__signpost__", CRM(crm.factory))
        assert query.build().column_descriptions[0]["entity"] is entity
        with pytest.raises(TypeError, match="their declared signpost"):
            pinned.build()
        monkeypatch.setattr(entity, "__signpost__", ERP(crm.factory))
        with pytest.raises(
            TypeError, match="__signpost__ must be an instance of CRM"
        ):
            query.build()

    @when("scoped and legacy source declarations are used in queries")
    def direct_sources(self, crm: CRM) -> tuple[tuple[SQLSource, bool], ...]:
        class DirectScoped(SQLEntity[int, CRM], table=False):
            __signpost__ = crm

        class AnyScoped(SQLEntity[int, Any], table=False):
            __signpost__ = crm

        return tuple(
            (entity.__signpost__, SQLQuery(entity).entity is entity)
            for entity in (DirectScoped, AnyScoped)
        )

    @then("direct source declarations retain the existing query constructor")
    def test_direct_source(
        self, crm: CRM, direct_sources: tuple[tuple[SQLSource, bool], ...]
    ) -> None:
        for source, same_entity in direct_sources:
            assert source is crm
            assert same_entity

    @when("inherited and direct entity declarations specify a foreign source")
    def foreign_declarations(
        self, crm: CRM
    ) -> tuple[tuple[str, ...], list[TypeError]]:
        source = ERP(crm.factory)
        tables = tuple(SQL_ENTITY_REGISTRY.metadata.tables)
        failures: list[TypeError] = []
        try:

            class InvalidScoped(CRMModel):
                __signpost__ = source
        except TypeError as error:
            failures.append(error)

        try:

            class InvalidDirect(SQLEntity[int, CRM]):
                __signpost__ = source
        except TypeError as error:
            failures.append(error)
        return tables, failures

    @then("a mismatched source is rejected before SQL mapping")
    def test_wrong_source(
        self, foreign_declarations: tuple[tuple[str, ...], list[TypeError]]
    ) -> None:
        tables, failures = foreign_declarations
        assert len(failures) == 2
        assert all(
            "__signpost__ must be an instance of CRM" in str(error)
            for error in failures
        )

        assert tuple(SQL_ENTITY_REGISTRY.metadata.tables) == tables
