import inspect
from typing import Annotated

import pytest

from fastsprout.core import DependencyInjector, Depends, inject_depends
from fastsprout.testing.core import given, then, when


class TestDependencyErrors:
    @given("an injector without configured providers")
    def injector(self) -> DependencyInjector:
        return DependencyInjector()

    @when("provider overrides create a recursive dependency")
    async def circular(
        self, injector: DependencyInjector, asynchronous: bool
    ) -> RuntimeError | None:
        def source() -> int:
            return 1

        def recursive(value: int = Depends(source)) -> int:
            return value

        injector.dependency_overrides[source] = recursive
        try:
            if asynchronous:
                await injector.aresolve(Depends(source), int)
            else:
                injector.resolve(Depends(source), int)
        except RuntimeError as error:
            return error
        return None

    @pytest.mark.parametrize("asynchronous", [False, True])
    @then("circular providers fail before executing the dependency")
    def test_circular(self, circular: RuntimeError | None) -> None:
        assert isinstance(circular, RuntimeError)
        assert "Circular dependency" in str(circular)

    @when("arguments are injected synchronously without an enclosing scope")
    def injected(self, injector: DependencyInjector) -> inspect.BoundArguments:
        def source() -> int:
            return 7

        def nested(value: int = Depends(source)) -> int:
            return value + 1

        def read(value: int = Depends(nested)) -> int:
            return value

        return injector.inject(read, (), {})

    @then("nested providers resolve before their arguments are bound")
    def test_direct_injection(self, injected: inspect.BoundArguments) -> None:
        assert injected.arguments == {"value": 8}

    @when("an implicit dependency has an ambiguous union annotation")
    def ambiguous(self, injector: DependencyInjector) -> TypeError | None:
        @injector
        def read(value: int | str = Depends()) -> int | str:
            return value

        try:
            read()
        except TypeError as error:
            return error
        return None

    @then("ambiguous annotations require an explicit provider")
    def test_ambiguous_provider(self, ambiguous: TypeError | None) -> None:
        assert isinstance(ambiguous, TypeError)
        assert "provider or a callable annotation" in str(ambiguous)

    @when("a synchronous invocation requests an asynchronous provider")
    def asynchronous(self, injector: DependencyInjector) -> TypeError | None:
        async def provider() -> int:
            return 42

        @injector
        def read(value: int = Depends(provider)) -> int:
            return value

        try:
            read()
        except TypeError as error:
            return error
        return None

    @then("the coroutine is rejected instead of leaking from a sync call")
    def test_async_in_sync(self, asynchronous: TypeError | None) -> None:
        assert isinstance(asynchronous, TypeError)
        assert "Async dependency needs async inject_depends" in str(
            asynchronous
        )


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
