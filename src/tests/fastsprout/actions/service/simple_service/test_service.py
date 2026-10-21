import asyncio
from typing import Annotated, assert_type
from weakref import ref

import pytest

from fastsprout.actions import Action, Service, action
from fastsprout.core import (
    ActionGroupable,
    Depends,
    Schema,
    dataclass,
    inject_depends,
)


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


async def test_service_inherits_actions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # given
    checks: list[str] = []

    def check() -> None:
        checks.append("check")

    monkeypatch.setattr(BaseHeroesService, "dependencies", [Depends(check)])
    heroes = HeroesService()

    # when
    result = await heroes.get(10)
    await heroes.get(20)
    await heroes.boost(StrengthenHero(10))

    # then
    assert isinstance(heroes, ActionGroupable)
    assert_type(result, StrengthenHero)
    assert result.power == 10
    assert checks == ["check"] * 4

    # when
    await HeroesService(dependencies=[]).get(10)

    # then
    assert checks == ["check"] * 4


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


async def test_service_can_compose_class_actions_and_bound_service_methods(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # given
    calls: list[str] = []

    def shared() -> None:
        calls.append("shared")

    def local() -> None:
        calls.append("local")

    class Strengthen(Action[StrengthenHero, StrengthenHero]):
        async def __call__(self, payload: StrengthenHero) -> StrengthenHero:
            calls.append("action")
            return StrengthenHero(payload.power + 1)

    strengthen = Strengthen(dependencies=[Depends(shared), Depends(local)])
    heroes = HeroesService()

    class ComposedService(Service):
        execute = strengthen
        boost = heroes.boost

    composed = ComposedService(dependencies=[Depends(shared)])

    # when
    first = await composed.execute(StrengthenHero(10))
    second = await composed.execute(StrengthenHero(20))

    # then
    assert_type(first, StrengthenHero)
    assert (first.power, second.power) == (11, 21)
    assert calls == ["shared", "local", "action"] * 2

    # when
    assert (await composed.boost(StrengthenHero(10))).power == 12

    # then
    assert calls[-1] == "shared"

    # given
    monkeypatch.setitem(
        inject_depends.dependency_overrides, strengthen, heroes.strengthen
    )
    result_dependency = Depends(composed.execute)

    @action(dependencies=[result_dependency])
    async def submit(
        payload: StrengthenHero, result: StrengthenHero = result_dependency
    ) -> StrengthenHero:
        return result

    # when
    calls.clear()
    result = await submit(StrengthenHero(10))

    # then
    assert result.power == 12
    assert calls == []


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


class TestServiceDependencies:
    @pytest.mark.parametrize("shared_instance", [False, True])
    async def test_class_and_instance_methods_preserve_owner(
        self, shared_instance: bool
    ) -> None:
        # given
        instances: list[Service] = []
        calls: list[tuple[Service, str, int]] = []

        class Checks(Service):
            def __init__(self, power: int = EXTRA_POWER) -> None:
                super().__init__()
                self.power = power
                instances.append(self)

            @action
            async def access(self, operation: str) -> None:
                calls.append((self, operation, self.power))

            @action
            async def audit(self, operation: str) -> None:
                calls.append((self, operation, self.power))

        checks = Checks(power=10) if shared_instance else None
        access = checks.access if checks is not None else Checks.access
        audit = checks.audit if checks is not None else Checks.audit

        @action(
            dependencies=[Depends(access), audit.dependency, access.dependency]
        )
        async def submit(operation: str) -> None:
            pass

        # when
        await submit("create")
        await submit("update")

        # then
        assert len(instances) == (1 if shared_instance else 2)
        assert [call[1] for call in calls] == [
            "create",
            "create",
            "update",
            "update",
        ]
        assert [call[2] for call in calls] == [10 if shared_instance else 2] * 4
        assert calls[0][0] is calls[1][0] is instances[0]
        assert calls[2][0] is calls[3][0] is instances[-1]
        assert (calls[0][0] is calls[2][0]) is shared_instance

    async def test_bound_method_keeps_call_signature(self) -> None:
        # given
        class Checks(Service):
            @action
            async def access(self, payload: StrengthenHero) -> StrengthenHero:
                return payload

        checks = Checks()
        reference = ref(checks)
        payload = StrengthenHero(10)

        # when
        result = await checks.access(payload)
        injected = await Checks.access(payload)

        # then
        assert_type(result, StrengthenHero)
        assert_type(injected, StrengthenHero)
        assert result is injected is payload
        del checks
        assert reference() is None

    async def test_registered_provider_supplies_singleton(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # given
        calls: list[Service] = []

        class Checks(Service):
            async def access(self) -> None:
                calls.append(self)

        checks = Checks()
        monkeypatch.setitem(
            inject_depends.dependency_providers, Checks, lambda: checks
        )

        @action(dependencies=[Depends(Checks.access)])
        async def submit() -> None:
            pass

        # when
        await submit()
        await submit()

        # then
        assert calls == [checks, checks]
