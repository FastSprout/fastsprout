from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from fastsprout.actions import DataS, Service, action
from fastsprout.core import Depends
from fastsprout.data import DataR
from fastsprout.testing.core import then, when

from .common import (
    HeroesService,
    OptionalTeamHero,
    OptionalTeamHeroCreate,
    SecretHero,
    SelectedHeroActions,
)

type ServiceCycle = tuple[
    HeroesService | SelectedHeroActions, bool, int, int, bool
]


@when("an inherited data service executes CRUD and custom actions")
async def custom_actions(
    prepared_tables: AsyncEngine,
    factory: type[HeroesService | SelectedHeroActions],
) -> ServiceCycle:
    heroes = factory()
    async with DataR() as datar:
        created = await heroes.create(
            SecretHero(name="Robin", secret="private"), datar=datar
        )
        found = await heroes.get(created.id, datar=datar) is not None
        strengthened = await heroes.strengthen(10)
        deleted = await heroes.delete(created.id, datar=datar)
        missing = await heroes.get(created.id, datar=datar) is None
    return heroes, found, strengthened, deleted, missing


@then("crud inherits operations alongside custom actions")
@pytest.mark.parametrize("factory", [HeroesService, SelectedHeroActions])
def test_crud_inherits_operations_alongside_custom_actions(
    custom_actions: ServiceCycle,
) -> None:
    heroes, found, strengthened, deleted, missing = custom_actions
    assert isinstance(heroes, Service)
    assert found
    assert strengthened == 11
    assert deleted == 1
    assert missing


@when("a parent action creates an entity and then fails")
async def aborted_action(
    prepared_tables: AsyncEngine,
) -> tuple[UUID, bool, ValueError | None]:
    heroes = HeroesService()
    created_ids: list[UUID] = []
    confirmed: list[bool] = []
    dependency = Depends()

    @action
    async def create_then_fail(datar: DataR = dependency) -> None:
        created = await heroes.create(
            SecretHero(name="Robin", secret="private")
        )
        created_ids.append(created.id)
        confirmed.append(await heroes.get(created.id, datar=datar) is not None)
        raise ValueError("Abort invocation")

    failure = None
    try:
        await create_then_fail()
    except ValueError as error:
        failure = error
    return created_ids[0], confirmed[0], failure


@then("nested crud actions share transaction and roll back together")
async def test_nested_crud_rolls_back_shared_transaction(
    aborted_action: tuple[UUID, bool, ValueError | None],
) -> None:
    identifier, confirmed, failure = aborted_action
    assert confirmed
    assert isinstance(failure, ValueError)
    assert str(failure) == "Abort invocation"
    assert await HeroesService().get(identifier) is None


@when("an entity is created from an explicit write DTO")
async def created_from_dto(prepared_tables: AsyncEngine) -> OptionalTeamHero:
    return await DataS(OptionalTeamHero).create(
        OptionalTeamHeroCreate(name="Batman", team=None)
    )


@then("create accepts write dto")
async def test_create_accepts_write_dto(
    created_from_dto: OptionalTeamHero,
) -> None:
    with pytest.raises(AttributeError, match="not accessible"):
        OptionalTeamHeroCreate(id=uuid4(), name="Batman")
    assert created_from_dto.name == "Batman"
    assert created_from_dto.team is None
    assert await DataS(OptionalTeamHero).get(created_from_dto.id) is not None
