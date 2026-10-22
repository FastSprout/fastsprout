from uuid import UUID, uuid4

import pytest
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncEngine

from fastsprout.actions import DataS
from fastsprout.core import ReadDTO
from fastsprout.testing.core import then, when

from ...common import loaded_query
from .common import (
    OptionalTeamHero,
    SecretHero,
    SecretHeroRead,
    SecretLeague,
    SecretTeam,
    SecretTeamRead,
    TeamHero,
)

type ReadCycle = tuple[
    SecretHeroRead, SecretHeroRead | None, SecretHeroRead, SecretHero | None
]


@when("a private entity is created, read, and updated through a read DTO")
async def read_cycle(prepared_tables: AsyncEngine) -> ReadCycle:
    heroes = DataS(SecretHero, read=SecretHeroRead)
    created = await heroes.create(SecretHero(name="Batman", secret="private"))
    found = await heroes.get(created.id)
    updated = await heroes.update(
        SecretHero(id=created.id, name="Robin", secret="replacement")
    )
    persisted = await DataS(SecretHero).get(created.id)
    return created, found, updated, persisted


@then("explicit read dto hides internal fields")
def test_explicit_read_dto_hides_internal_fields(read_cycle: ReadCycle) -> None:
    created, found, updated, persisted = read_cycle
    assert found is not None
    for public in (created, found, updated):
        assert isinstance(public, ReadDTO)
        with pytest.raises(AttributeError, match="not accessible"):
            public.__getattribute__("secret")
    assert sa_inspect(type(found), raiseerr=False) is None
    assert found.name == "Batman"
    assert "secret" not in vars(found)
    assert updated.name == "Robin"
    assert persisted is not None
    assert persisted.name == "Robin"
    assert persisted.secret == "private"


@when("a related entity is read and updated at one or two levels")
async def related_cycle(
    prepared_tables: AsyncEngine, deep: bool
) -> tuple[SecretTeam | SecretLeague, TeamHero | None]:
    team = SecretTeam(name="Justice League", secret="private")
    if deep:
        team.secret = "team secret"
        team.league = SecretLeague(name="World", secret="league secret")
    heroes = DataS(TeamHero)
    created = await heroes.create(TeamHero(name="Batman", team=team))
    found = await heroes.get(loaded_query(TeamHero, created.id))
    assert found is not None
    related = found.team.league if deep else found.team
    assert related is not None
    before = related.model_copy()
    if deep:
        related.name = "International"
        await heroes.update(found)
    else:
        await heroes.update(
            found.model_copy(
                update={
                    "team": found.team.model_copy(
                        update={"name": "Justice League International"}
                    )
                }
            )
        )
    return before, await heroes.get(loaded_query(TeamHero, created.id))


@pytest.mark.parametrize(
    "deep, entity, name, secret, updated",
    [
        (
            False,
            SecretTeam,
            "Justice League",
            "private",
            "Justice League International",
        ),
        (True, SecretLeague, "World", "league secret", "International"),
    ],
)
@then("related entities retain their ORM type, private fields, and changes")
def test_related_entities(
    related_cycle: tuple[SecretTeam | SecretLeague, TeamHero | None],
    deep: bool,
    entity: type[SecretTeam | SecretLeague],
    name: str,
    secret: str,
    updated: str,
) -> None:
    before, loaded = related_cycle
    assert not TeamHero.__table__.c.team_id.nullable
    assert type(before) is entity
    assert sa_inspect(type(before), raiseerr=False) is not None
    assert (before.name, before.secret) == (name, secret)
    assert loaded is not None
    related = loaded.team.league if deep else loaded.team
    assert related is not None
    assert related.name == updated


@when("an optional relation is replaced and subsequently cleared")
async def optional_cycle(
    prepared_tables: AsyncEngine,
) -> tuple[SecretTeam, tuple[UUID, str], OptionalTeamHero | None]:
    heroes, teams = DataS(OptionalTeamHero), DataS(SecretTeam)
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
    assert loaded is not None and loaded.team is not None
    before_clear = loaded.team.id, loaded.team.name
    loaded.team = None
    await heroes.update(loaded)
    return (
        replacement,
        before_clear,
        await heroes.get(loaded_query(OptionalTeamHero, created.id)),
    )


@then("update replaces and clears relation")
async def test_update_replaces_and_clears_relation(
    optional_cycle: tuple[
        SecretTeam, tuple[UUID, str], OptionalTeamHero | None
    ],
) -> None:
    replacement, before_clear, cleared = optional_cycle
    assert before_clear == (replacement.id, "Outsiders")
    assert cleared is not None
    assert cleared.team is None
    assert (
        await DataS(SecretTeam).get(loaded_query(SecretTeam, replacement.id))
        is not None
    )


@when("a nested update references a missing related entity")
async def rejected_graph(
    prepared_tables: AsyncEngine,
) -> tuple[TeamHero, LookupError | None]:
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
    try:
        await heroes.update(found)
    except LookupError as error:
        return created, error
    return created, None


@then("nested update failure rolls back entire graph")
async def test_nested_update_failure_rolls_back_entire_graph(
    rejected_graph: tuple[TeamHero, LookupError | None],
) -> None:
    created, failure = rejected_graph
    assert isinstance(failure, LookupError)
    assert "No SecretTeam" in str(failure)
    loaded = await DataS(TeamHero).get(loaded_query(TeamHero, created.id))
    assert loaded is not None
    assert loaded.name == "Batman"
    assert loaded.team.id == created.team.id
    assert loaded.team.name == "Justice League"


@when("a graph with explicit entity IDs is created")
async def explicit_ids(
    prepared_tables: AsyncEngine,
) -> tuple[TeamHero, TeamHero]:
    hero = TeamHero(
        name="Batman",
        team=SecretTeam(id=uuid4(), name="Justice League", secret="private"),
    )
    return hero, await DataS(TeamHero).create(hero)


@then("create preserves explicit entity ids")
def test_create_preserves_explicit_entity_ids(
    explicit_ids: tuple[TeamHero, TeamHero],
) -> None:
    hero, created = explicit_ids
    assert created.id == hero.id
    assert created.team.id == hero.team.id


@when("a related read DTO with a stale name is used as a reference")
async def referenced_team(
    prepared_tables: AsyncEngine,
) -> tuple[SecretTeamRead, TeamHero]:
    teams = DataS(SecretTeam, read=SecretTeamRead)
    team = await teams.create(
        SecretTeam(name="Justice League", secret="private")
    )
    team.name = "A stale snapshot"
    created = await DataS(TeamHero).create(TeamHero(name="Batman", team=team))
    return team, created


@then("create reuses related read dto as reference")
def test_create_reuses_related_read_dto_as_reference(
    referenced_team: tuple[SecretTeamRead, TeamHero],
) -> None:
    team, created = referenced_team
    assert created.team.id == team.id
    assert created.team.name == "Justice League"
    assert type(created.team) is SecretTeam
    assert created.team.secret == "private"
