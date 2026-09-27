from typing import Annotated

from fastsprout.core import DependencyInjector, Depends


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
