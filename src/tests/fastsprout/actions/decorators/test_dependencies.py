from __future__ import annotations

from typing import Annotated, assert_type

import pytest

from fastsprout.actions import Action, Service, action
from fastsprout.core import Depends, Schema, dataclass, inject_depends


@dataclass
class Input(Schema):
    value: int


@dataclass
class Actor(Schema):
    allowed: bool


def current_actor() -> Actor:
    return Actor(allowed=True)


async def test_function_dependencies_accept_different_signatures() -> None:
    calls: list[str] = []

    def check_configuration() -> str:
        calls.append("configuration")
        return "ready"

    async def check_access(
        actor: Annotated[Actor, Depends(current_actor)],
    ) -> None:
        calls.append("access")
        assert actor.allowed

    def check_payload(payload: Input) -> None:
        calls.append("payload")
        assert payload.value > 0

    @action(
        dependencies=[
            Depends(check_configuration),
            Depends(check_access),
            Depends(check_payload),
        ]
    )
    async def execute(payload: Input) -> int:
        calls.append("action")
        return payload.value

    result = await execute(Input(42))
    assert_type(result, int)
    assert result == 42
    assert calls == ["configuration", "access", "payload", "action"]


async def test_dependencies_reject_before_executing_action() -> None:
    async def reject() -> None:
        raise PermissionError("Forbidden")

    @action(dependencies=[Depends(reject)])
    async def execute(payload: Input) -> int:
        raise AssertionError("Rejected action ran")

    with pytest.raises(PermissionError, match="Forbidden"):
        await execute(Input(42))


async def test_class_action_uses_the_same_dependency_execution() -> None:
    values: list[int] = []

    def check(payload: Input) -> None:
        values.append(payload.value)

    class Execute(Action[Input, Input]):
        async def __call__(self, payload: Input) -> Input:
            return Input(payload.value * 2)

    execute = Execute(dependencies=[Depends(check)])
    result = await execute(Input(21))
    assert_type(result, Input)
    assert result.value == 42
    assert values == [21]


async def test_service_and_function_dependencies_share_cache() -> None:
    calls: list[str] = []

    def shared() -> Actor:
        calls.append("shared")
        return Actor(allowed=True)

    def local() -> None:
        calls.append("local")

    @action(dependencies=[Depends(shared), Depends(local)])
    async def execute(payload: Input) -> int:
        return payload.value

    class Documents(Service):
        run = execute

        async def render(self, payload: Input) -> int:
            return payload.value

    documents = Documents(dependencies=[Depends(shared)])
    assert await documents.run(Input(42)) == 42
    assert calls == ["shared", "local"]
    calls.clear()
    assert await documents.render(Input(42)) == 42
    assert calls == ["shared"]


async def test_dependencies_apply_to_overridden_service_methods() -> None:
    operations: list[str] = []

    def check(operation: str) -> None:
        operations.append(operation)

    class BaseDocuments(Service):
        async def render(self, payload: Input) -> int:
            return payload.value

    class Documents(BaseDocuments):
        async def render(self, payload: Input) -> int:
            return payload.value * 2

    documents = Documents(dependencies=[Depends(check)])
    assert await documents.render(Input(21)) == 42
    assert operations == ["render"]


async def test_dependencies_honor_use_cache_false_and_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[int] = []

    def provider() -> int:
        raise AssertionError("Overridden provider ran")

    def override() -> int:
        calls.append(len(calls))
        return calls[-1]

    monkeypatch.setitem(inject_depends.dependency_overrides, provider, override)

    @action(
        dependencies=[
            Depends(provider, use_cache=False),
            Depends(provider, use_cache=False),
        ]
    )
    async def execute() -> None:
        pass

    await execute()
    assert calls == [0, 1]


async def test_action_parameter_and_list_share_nested_dependency() -> None:
    actors: list[Actor] = []

    async def current_actor() -> Actor:
        actor = Actor(allowed=True)
        actors.append(actor)
        return actor

    dependency = Depends(current_actor)

    def check(actor: Actor = dependency) -> None:
        assert actor is actors[0]

    @action(dependencies=[Depends(check)])
    async def execute(actor: Actor = dependency) -> Actor:
        return actor

    assert await execute() is actors[0]
    assert len(actors) == 1


async def test_dependency_receives_action_argument_default() -> None:
    counts: list[int] = []

    def check(count: int) -> None:
        counts.append(count)

    @action(dependencies=[Depends(check)])
    async def execute(count: int = 42) -> int:
        return count

    assert await execute() == 42
    assert counts == [42]


async def test_explicit_provider_is_not_replaced_by_matching_argument() -> None:
    main_actor = Actor(allowed=True)
    other_actor = Actor(allowed=False)

    def current_actor() -> Actor:
        return main_actor

    def other_provider() -> Actor:
        return other_actor

    other = Depends(other_provider)
    current = Depends(current_actor)

    def check(actor: Actor = other) -> None:
        assert actor is other_actor

    @action(dependencies=[Depends(check)])
    async def execute(actor: Actor = current) -> Actor:
        return actor

    assert await execute() is main_actor


async def test_parameter_dependency_receives_payload_and_shares_list_cache() -> (
    None
):
    values: list[int] = []

    def validate(payload: Input) -> int:
        values.append(payload.value)
        return payload.value * 2

    marker = Depends(validate)

    @action(dependencies=[marker])
    async def execute(payload: Input, checked: int = marker) -> int:
        return checked

    assert await execute(Input(21)) == 42
    assert values == [21]


async def test_annotated_parameter_and_list_share_explicit_provider() -> None:
    calls: list[Actor] = []

    def check(actor: Annotated[Actor, Depends(current_actor)]) -> Actor:
        calls.append(actor)
        return actor

    marker = Depends(check)

    @action(dependencies=[marker])
    async def execute(actor: Actor, checked: Actor = marker) -> Actor:
        assert checked is not actor
        return checked

    result = await execute(Actor(allowed=False))
    assert result.allowed
    assert calls == [result]
