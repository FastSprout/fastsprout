import inspect
from typing import Annotated

from fastsprout.core import DependencyInjector, Depends, inject_depends


def test_injector_overrides_provider_and_caches_per_call():
    injector = DependencyInjector()
    calls = 0

    def provider() -> int:
        nonlocal calls
        calls += 1
        return calls

    @injector
    def use(first: int = Depends(provider), second: int = Depends(provider)):
        return first, second

    assert use() == (1, 1)
    assert use() == (2, 2)
    assert use(first=9) == (9, 3)

    injector.dependency_overrides[provider] = lambda: 42
    assert use() == (42, 42)


async def test_injector_resolves_async_and_nested_dependencies():
    injector = DependencyInjector()

    async def source() -> int:
        return 3

    async def nested(value: int = Depends(source)) -> int:
        return value + 1

    @injector
    async def use(value: Annotated[int, Depends(nested)]) -> int:
        return value

    assert await use() == 4


def test_depends_without_provider_uses_annotation():
    injector = DependencyInjector()

    class Service:
        pass

    default_service: Service = Depends()

    @injector
    def use(service: Service = default_service) -> Service:
        return service

    assert isinstance(use(), Service)


@inject_depends
async def test_dependencies_share_cache_only_within_one_operation():
    calls: list[str] = []

    def source() -> int:
        calls.append("source")
        return 7

    def nested(value: int = Depends(source)) -> int:
        calls.append("nested")
        return value

    def check(operation: str, value: int = Depends(nested)) -> None:
        assert value == 7
        calls.append(operation)

    async def execute(operation: str) -> None:
        pass

    dependencies = [Depends(check), Depends(check)]
    await inject_depends.ainject(
        execute,
        ("create",),
        {},
        extra_dependencies=dependencies,
        supplied=inspect.signature(execute).bind("create"),
    )
    await inject_depends.ainject(
        execute,
        ("delete",),
        {},
        extra_dependencies=dependencies,
        supplied=inspect.signature(execute).bind("delete"),
    )
    assert calls == ["source", "nested", "create", "source", "nested", "delete"]
