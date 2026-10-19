from uuid import UUID, uuid4

import pytest
from sqlalchemy import inspect as sa_inspect
from sqlalchemy import select

from fastsprout.actions import DataS, Service, action
from fastsprout.core import (
    Depends,
    ReadDTO,
)
from fastsprout.data import DataR, sql
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY
from fastsprout.testing.core import when_then

from ...common import loaded_query
from .common import (
    HeroesService,
    OptionalTeamHero,
    OptionalTeamHeroCreate,
    SecretHero,
    SecretHeroRead,
    SecretLeague,
    SecretTeam,
    SecretTeamRead,
    SelectedHeroActions,
    TeamHero,
    engine,
)


@when_then("explicit read dto hides internal fields")
async def test_explicit_read_dto_hides_internal_fields() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

    heroes = DataS(SecretHero, read=SecretHeroRead)
    created = await heroes.create(SecretHero(name="Batman", secret="private"))
    assert isinstance(created, ReadDTO)
    with pytest.raises(AttributeError, match="not accessible"):
        created.__getattribute__("secret")
    found = await heroes.get(created.id)

    assert found is not None
    assert isinstance(found, ReadDTO)
    assert sa_inspect(type(found), raiseerr=False) is None
    assert found.name == "Batman"
    with pytest.raises(AttributeError, match="not accessible"):
        found.__getattribute__("secret")
    assert "secret" not in vars(found)

    updated = await heroes.update(
        SecretHero(id=created.id, name="Robin", secret="replacement")
    )
    assert isinstance(updated, ReadDTO)
    assert updated.name == "Robin"
    with pytest.raises(AttributeError, match="not accessible"):
        updated.__getattribute__("secret")

    async with DataR() as datar:
        persisted = await datar.ability(SecretHero).find_first(
            sql.SQLQuery(
                entity=SecretHero,
                statement=select(SecretHero).where(
                    SecretHero.__table__.c.id == created.id
                ),
            )
        )
    assert persisted is not None
    assert persisted.name == "Robin"
    assert persisted.secret == "private"

    await engine.dispose()


@when_then("nested entities are not converted to dtos")
async def test_nested_entities_are_not_converted_to_dtos() -> None:
    assert not TeamHero.__table__.c.team_id.nullable
    async with engine.begin() as connection:
        await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

    heroes = DataS(TeamHero)
    created = await heroes.create(
        TeamHero(
            name="Batman",
            team=SecretTeam(name="Justice League", secret="private"),
        )
    )
    found = await heroes.get(loaded_query(TeamHero, created.id))
    assert found is not None
    assert type(found.team) is SecretTeam
    assert sa_inspect(type(found.team), raiseerr=False) is not None
    assert found.team.name == "Justice League"
    assert found.team.secret == "private"

    await heroes.update(
        found.model_copy(
            update={
                "team": found.team.model_copy(
                    update={"name": "Justice League International"}
                )
            }
        )
    )
    loaded = await heroes.get(loaded_query(TeamHero, created.id))
    assert loaded is not None
    assert loaded.team.name == "Justice League International"
    await engine.dispose()


@when_then("deep graph read and update")
async def test_deep_graph_read_and_update() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

    heroes = DataS(TeamHero)
    created = await heroes.create(
        TeamHero(
            name="Batman",
            team=SecretTeam(
                name="Justice League",
                secret="team secret",
                league=SecretLeague(name="World", secret="league secret"),
            ),
        )
    )
    found = await heroes.get(loaded_query(TeamHero, created.id))
    assert found is not None
    league = found.team.league
    assert league is not None
    assert league.name == "World"
    assert type(league) is SecretLeague
    assert league.secret == "league secret"

    league.name = "International"
    await heroes.update(found)
    loaded = await heroes.get(loaded_query(TeamHero, created.id))
    assert loaded is not None
    assert loaded.team.league is not None
    assert loaded.team.league.name == "International"
    await engine.dispose()


@when_then("update replaces and clears relation")
async def test_update_replaces_and_clears_relation() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

    heroes = DataS(OptionalTeamHero)
    teams = DataS(SecretTeam)
    created = await heroes.create(
        OptionalTeamHero(
            name="Batman",
            team=SecretTeam(name="Justice League", secret="original"),
        )
    )
    replacement = await teams.create(
        SecretTeam(name="Outsiders", secret="replacement")
    )
    found = await heroes.get(loaded_query(OptionalTeamHero, created.id))
    assert found is not None
    found.team = await teams.get(loaded_query(SecretTeam, replacement.id))
    await heroes.update(found)
    loaded = await heroes.get(loaded_query(OptionalTeamHero, created.id))
    assert loaded is not None
    assert loaded.team is not None
    assert loaded.team.id == replacement.id
    assert loaded.team.name == "Outsiders"

    loaded.team = None
    await heroes.update(loaded)
    cleared = await heroes.get(loaded_query(OptionalTeamHero, created.id))
    assert cleared is not None
    assert cleared.team is None
    assert await teams.get(loaded_query(SecretTeam, replacement.id)) is not None
    await engine.dispose()


@when_then("nested update failure rolls back entire graph")
async def test_nested_update_failure_rolls_back_entire_graph() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

    heroes = DataS(TeamHero)
    created = await heroes.create(
        TeamHero(
            name="Batman",
            team=SecretTeam(name="Justice League", secret="private"),
        )
    )
    found = await heroes.get(loaded_query(TeamHero, created.id))
    assert found is not None
    found.name = "Robin"
    found.team.id = uuid4()

    with pytest.raises(LookupError, match="No SecretTeam"):
        await heroes.update(found)

    loaded = await heroes.get(loaded_query(TeamHero, created.id))
    assert loaded is not None
    assert loaded.name == "Batman"
    assert loaded.team.id == created.team.id
    assert loaded.team.name == "Justice League"
    await engine.dispose()


@when_then("create preserves explicit entity ids")
async def test_create_preserves_explicit_entity_ids() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

    heroes = DataS(TeamHero)
    hero = TeamHero(
        name="Batman",
        team=SecretTeam(id=uuid4(), name="Justice League", secret="private"),
    )
    created = await heroes.create(hero)
    assert created.id == hero.id
    assert created.team.id == hero.team.id
    await engine.dispose()


@when_then("create reuses related read dto as reference")
async def test_create_reuses_related_read_dto_as_reference() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

    teams = DataS(SecretTeam, read=SecretTeamRead)
    team = await teams.create(
        SecretTeam(name="Justice League", secret="private")
    )
    team.name = "A stale snapshot"
    heroes = DataS(TeamHero)
    created = await heroes.create(TeamHero(name="Batman", team=team))

    assert created.team.id == team.id
    assert created.team.name == "Justice League"
    assert type(created.team) is SecretTeam
    assert created.team.secret == "private"
    await engine.dispose()


@when_then("crud inherits operations alongside custom actions")
@pytest.mark.parametrize("factory", [HeroesService, SelectedHeroActions])
async def test_crud_inherits_operations_alongside_custom_actions(
    factory: type[HeroesService | SelectedHeroActions],
) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)
    heroes = factory()
    assert isinstance(heroes, Service)
    async with DataR() as datar:
        created = await heroes.create(
            SecretHero(name="Robin", secret="private"), datar=datar
        )
        assert await heroes.get(created.id, datar=datar) is not None
        assert await heroes.strengthen(10) == 11
        assert await heroes.delete(created.id, datar=datar) == 1
        assert await heroes.get(created.id, datar=datar) is None
    await engine.dispose()


@when_then("nested crud actions share transaction and roll back together")
async def test_nested_crud_rolls_back_shared_transaction() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)
    heroes = HeroesService()
    created_ids: list[UUID] = []
    dependency = Depends()

    @action
    async def create_then_fail(datar: DataR = dependency) -> None:
        created = await heroes.create(
            SecretHero(name="Robin", secret="private")
        )
        created_ids.append(created.id)
        assert await heroes.get(created.id, datar=datar) is not None
        raise ValueError("Abort invocation")

    with pytest.raises(ValueError, match="Abort invocation"):
        await create_then_fail()
    assert await heroes.get(created_ids[0]) is None
    await engine.dispose()


@when_then("create accepts write dto")
async def test_create_accepts_write_dto() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)
    heroes = DataS(OptionalTeamHero)
    with pytest.raises(AttributeError, match="not accessible"):
        OptionalTeamHeroCreate(id=uuid4(), name="Batman")
    created = await heroes.create(
        OptionalTeamHeroCreate(name="Batman", team=None)
    )
    assert created.name == "Batman"
    assert created.team is None
    assert await heroes.get(created.id) is not None
    await engine.dispose()
