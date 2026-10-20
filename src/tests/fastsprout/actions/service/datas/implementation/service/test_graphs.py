from uuid import UUID, uuid4

import pytest
from sqlalchemy import inspect as sa_inspect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from fastsprout.actions import DataS
from fastsprout.core import ReadDTO, dataclass
from fastsprout.data import DataR, sql
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


@dataclass(frozen=True)
class SecretSnapshot[E]:
    entity: type[E]
    name: str
    secret: str


@when("a private entity is created, read, and updated through a read DTO")
async def read_cycle(prepared_tables: AsyncEngine) -> ReadCycle:
    heroes = DataS(SecretHero, read=SecretHeroRead)
    created = await heroes.create(SecretHero(name="Batman", secret="private"))
    found = await heroes.get(created.id)
    updated = await heroes.update(
        SecretHero(id=created.id, name="Robin", secret="replacement")
    )
    async with DataR() as datar:
        persisted = await datar.ability(SecretHero).find_first(
            sql.SQLQuery(
                entity=SecretHero,
                statement=select(SecretHero).where(
                    SecretHero.__table__.c.id == created.id
                ),
            )
        )
    return created, found, updated, persisted


@then("explicit read dto hides internal fields")
def test_explicit_read_dto_hides_internal_fields(read_cycle: ReadCycle) -> None:
    created, found, updated, persisted = read_cycle
    assert isinstance(created, ReadDTO)
    with pytest.raises(AttributeError, match="not accessible"):
        created.__getattribute__("secret")
    assert found is not None
    assert isinstance(found, ReadDTO)
    assert sa_inspect(type(found), raiseerr=False) is None
    assert found.name == "Batman"
    with pytest.raises(AttributeError, match="not accessible"):
        found.__getattribute__("secret")
    assert "secret" not in vars(found)
    assert isinstance(updated, ReadDTO)
    assert updated.name == "Robin"
    with pytest.raises(AttributeError, match="not accessible"):
        updated.__getattribute__("secret")
    assert persisted is not None
    assert persisted.name == "Robin"
    assert persisted.secret == "private"


@when("a related entity is created, read, and updated through its parent")
async def related_cycle(
    prepared_tables: AsyncEngine,
) -> tuple[SecretSnapshot[SecretTeam], TeamHero | None]:
    heroes = DataS(TeamHero)
    created = await heroes.create(
        TeamHero(
            name="Batman",
            team=SecretTeam(name="Justice League", secret="private"),
        )
    )
    found = await heroes.get(loaded_query(TeamHero, created.id))
    assert found is not None
    before = SecretSnapshot(
        type(found.team), found.team.name, found.team.secret
    )
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
    return before, loaded


@then("nested entities are not converted to dtos")
def test_nested_entities_are_not_converted_to_dtos(
    related_cycle: tuple[SecretSnapshot[SecretTeam], TeamHero | None],
) -> None:
    before, loaded = related_cycle
    assert not TeamHero.__table__.c.team_id.nullable
    assert before.entity is SecretTeam
    assert sa_inspect(before.entity, raiseerr=False) is not None
    assert before.name == "Justice League"
    assert before.secret == "private"
    assert loaded is not None
    assert loaded.team.name == "Justice League International"


@when("a deeply related league is read and then updated through its hero")
async def league_cycle(
    prepared_tables: AsyncEngine,
) -> tuple[SecretSnapshot[SecretLeague], TeamHero | None]:
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
    before = SecretSnapshot(type(league), league.name, league.secret)
    league.name = "International"
    await heroes.update(found)
    return before, await heroes.get(loaded_query(TeamHero, created.id))


@then("deep graph read and update")
def test_deep_graph_read_and_update(
    league_cycle: tuple[SecretSnapshot[SecretLeague], TeamHero | None],
) -> None:
    before, loaded = league_cycle
    assert before.name == "World"
    assert before.entity is SecretLeague
    assert before.secret == "league secret"
    assert loaded is not None
    assert loaded.team.league is not None
    assert loaded.team.league.name == "International"


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
