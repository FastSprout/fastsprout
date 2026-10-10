import asyncio
from typing import Annotated, assert_type

from fastsprout.actions import Action, Service, action
from fastsprout.core import BaseActionGroup, Depends, Schema, dataclass


@dataclass
class StrengthenHero(Schema):
    power: int


def extra_power() -> int:
    return 2


EXTRA_POWER = Depends(extra_power)


class BaseHeroesService(Service):
    async def get(self, identifier: int) -> StrengthenHero:
        return StrengthenHero(identifier)


class HeroesService(BaseHeroesService):
    async def strengthen(
        self,
        payload: StrengthenHero,
        power: int = EXTRA_POWER,
    ) -> StrengthenHero:
        return StrengthenHero(payload.power + power)

    async def boost(self, payload: StrengthenHero) -> StrengthenHero:
        return await self.strengthen(payload)


async def test_service_inherits_actions() -> None:
    heroes = HeroesService()
    assert isinstance(heroes, BaseActionGroup)
    result = await heroes.get(10)
    assert_type(result, StrengthenHero)
    assert result.power == 10


async def test_service_methods_keep_typing_and_dependency_injection() -> None:
    heroes = HeroesService()
    result = await heroes.strengthen(StrengthenHero(10))
    assert_type(result, StrengthenHero)
    assert result.power == 12
    overridden = await heroes.strengthen(StrengthenHero(10), power=4)
    assert overridden.power == 14


async def test_function_alias_resolves_annotated_dependency() -> None:
    @action
    async def render(
        payload: StrengthenHero,
        power: Annotated[int, Depends(extra_power)] = 0,
    ) -> int:
        return payload.power + power

    class DocumentsService(Service):
        generate = render

    result = await DocumentsService().generate(StrengthenHero(10))
    assert_type(result, int)
    assert result == 12


async def test_unused_service_dependency_is_not_resolved() -> None:
    def unavailable() -> StrengthenHero:
        raise AssertionError("Unused dependencies must not be resolved")

    dependency = Depends(unavailable)

    class DocumentsService(Service):
        document: StrengthenHero = dependency

        async def render(self, payload: str) -> str:
            return payload

    assert await DocumentsService().render("document") == "document"


async def test_service_can_compose_class_actions_and_bound_service_methods() -> (
    None
):
    class Strengthen(Action[StrengthenHero, StrengthenHero]):
        async def __call__(self, payload: StrengthenHero) -> StrengthenHero:
            return StrengthenHero(payload.power + 1)

    heroes = HeroesService()

    class ComposedService(Service):
        strengthen = Strengthen()
        boost = heroes.boost

    composed = ComposedService()
    assert (await composed.strengthen(StrengthenHero(10))).power == 11
    assert (await composed.boost(StrengthenHero(10))).power == 12


async def test_concurrent_actions_resolve_cached_dependency_once() -> None:
    calls: list[StrengthenHero] = []

    async def provide() -> StrengthenHero:
        value = StrengthenHero(len(calls))
        calls.append(value)
        await asyncio.sleep(0)
        return value

    dependency = Depends(provide)

    @action
    async def child(value: StrengthenHero = dependency) -> StrengthenHero:
        return value

    @action
    async def parent() -> tuple[StrengthenHero, StrengthenHero]:
        first, second = await asyncio.gather(child(), child())
        return first, second

    first, second = await parent()
    assert first is second
    assert calls == [first]
