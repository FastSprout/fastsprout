import asyncio
import inspect
from collections.abc import AsyncGenerator, Callable, Generator, Sequence
from functools import wraps
from typing import Annotated, Any, cast, get_args, get_origin, get_type_hints
from uuid import UUID

from .bindings import bind_arguments, cache_key, dependency_key, enter_provider
from .marker import DependsClass
from .resolver import DependencyResolver
from .scope import (
    async_invocation_scope,
    current_dependency_cache,
    invocation_scope,
    resolve_yield,
)

__all__ = ["DependencyInjector", "Depends", "DependsClass", "inject_depends"]


def Depends(  # noqa: N802  # The public dependency marker follows FastAPI naming.
    dependency: Callable[..., Any] | None = None,
    *,
    use_cache: bool = True,
) -> Any:
    return DependsClass(dependency=dependency, use_cache=use_cache)


class DependencyInjector:
    """Resolve Depends providers with per-call caching and callable overrides."""

    def __init__(self) -> None:
        self.dependency_providers: dict[
            Callable[..., Any], Callable[..., Any]
        ] = {}
        self.dependency_overrides: dict[
            Callable[..., Any], Callable[..., Any]
        ] = {}

    @staticmethod
    def marker(
        parameter: inspect.Parameter, annotation: Any
    ) -> tuple[Any, Any]:
        if isinstance(parameter.default, DependsClass | DependencyResolver):
            return parameter.default, annotation
        if get_origin(annotation) is Annotated:
            value_type, *metadata = get_args(annotation)
            for item in metadata:
                if isinstance(item, DependsClass | DependencyResolver):
                    return item, value_type
        return None, annotation

    def provider(self, marker: Any, annotation: Any) -> Callable[..., Any]:
        dependency = marker.dependency or annotation
        if not callable(dependency):
            raise TypeError(
                "Depends() needs a provider or a callable annotation"
            )
        sources = (dependency, inspect.unwrap(dependency))
        for providers in (self.dependency_overrides, self.dependency_providers):
            for source in sources:
                if source in providers:
                    return providers[source]
        return dependency

    def dependency_key[**P, R](
        self, provider: Callable[P, R], active: frozenset[int] = frozenset()
    ) -> UUID | None:
        enter_provider(id(provider), seen := set(active))
        bound, dependencies = self.arguments(provider, (), {})
        key = dependency_key(bound.signature, provider)
        for _, marker, annotation in dependencies:
            if isinstance(marker, DependsClass):
                nested = self.dependency_key(
                    self.provider(marker, annotation), frozenset(seen)
                )
                key = key or nested
        return key

    @staticmethod
    def call_sync(
        provider: Callable[..., Any], bound: inspect.BoundArguments
    ) -> Any:
        value = provider(*bound.args, **bound.kwargs)
        if inspect.isawaitable(value):
            if inspect.iscoroutine(value):
                value.close()
            raise TypeError("Async dependency needs async inject_depends")
        return value

    @staticmethod
    async def call_async(
        provider: Callable[..., Any], bound: inspect.BoundArguments
    ) -> Any:
        value = provider(*bound.args, **bound.kwargs)
        if isinstance(value, AsyncGenerator | Generator):
            return await resolve_yield(value)
        if inspect.isawaitable(value):
            return await value
        return value

    def arguments(
        self,
        function: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        supplied: inspect.BoundArguments | None = None,
    ) -> tuple[inspect.BoundArguments, list[tuple[str, Any, Any]]]:
        signature = inspect.signature(function)
        target = inspect.unwrap(function)
        if not inspect.isroutine(target) and not inspect.isclass(target):
            target = type(target).__call__
        hints = get_type_hints(target, include_extras=True)
        parameters = [
            parameter.replace(annotation=hints.get(name, parameter.annotation))
            for name, parameter in signature.parameters.items()
        ]
        bound = signature.replace(parameters=parameters).bind_partial(
            *args, **kwargs
        )
        self.bind(bound, supplied)
        bind_arguments(bound)
        dependencies = []
        for name, parameter in signature.parameters.items():
            if name in bound.arguments:
                continue
            marker, value_type = self.marker(
                parameter, hints.get(name, parameter.annotation)
            )
            if marker is not None:
                dependencies.append((name, marker, value_type))
        return bound, dependencies

    def bind(
        self,
        bound: inspect.BoundArguments,
        supplied: inspect.BoundArguments | None,
    ) -> None:
        if supplied is None:
            return
        parameters = bound.signature.parameters
        for name in parameters.keys() & supplied.arguments.keys() - {"self"}:
            value = supplied.arguments[name]
            if isinstance(value, DependsClass | DependencyResolver):
                continue
            parameter = parameters[name]
            marker, _ = self.marker(parameter, parameter.annotation)
            if marker is None or (
                isinstance(marker, DependsClass) and marker.dependency is None
            ):
                bound.arguments.setdefault(name, value)

    def resolve_dependency(
        self,
        marker: Any,
        annotation: Any,
        cache: dict[object, Any],
        active: set[Callable[..., Any]],
    ) -> Any:
        if isinstance(marker, DependencyResolver):
            return marker.resolve(
                annotation,
                lambda provider: self.resolve_dependency(
                    DependsClass(provider), annotation, cache, active
                ),
            )
        provider = self.provider(marker, annotation)
        bound, dependencies = self.arguments(provider, (), {})
        key = cache_key(self, provider, self.dependency_key(provider))
        if marker.use_cache and key in cache:
            return cache[key]
        enter_provider(provider, active)
        try:
            for name, nested, value_type in dependencies:
                bound.arguments[name] = self.resolve_dependency(
                    nested, value_type, cache, active
                )
            value = self.call_sync(provider, bound)
            if marker.use_cache:
                cache[key] = value
            return value
        finally:
            active.remove(provider)

    async def aresolve_dependency(
        self,
        marker: Any,
        annotation: Any,
        cache: dict[object, Any],
        active: set[Callable[..., Any]],
        supplied: inspect.BoundArguments | None = None,
    ) -> Any:
        if isinstance(marker, DependencyResolver):
            return await marker.aresolve(
                annotation,
                lambda provider: self.aresolve_dependency(
                    DependsClass(provider), annotation, cache, active, supplied
                ),
            )
        provider = self.provider(marker, annotation)
        bound, dependencies = self.arguments(provider, (), {}, supplied)
        key = cache_key(self, provider, self.dependency_key(provider))
        enter_provider(provider, active)
        try:
            async with cache.setdefault((key, "lock"), asyncio.Lock()):
                if marker.use_cache and key in cache:
                    return cache[key]
                for name, nested, value_type in dependencies:
                    bound.arguments[name] = await self.aresolve_dependency(
                        nested, value_type, cache, active, supplied
                    )
                value = await self.call_async(provider, bound)
                if marker.use_cache:
                    cache[key] = value
                return value
        finally:
            active.remove(provider)

    def resolve(self, marker: Any, annotation: Any) -> Any:
        cache = current_dependency_cache()
        return self.resolve_dependency(
            marker, annotation, cache if cache is not None else {}, set()
        )

    async def aresolve(self, marker: Any, annotation: Any) -> Any:
        cache = current_dependency_cache()
        return await self.aresolve_dependency(
            marker, annotation, cache if cache is not None else {}, set()
        )

    def inject(
        self,
        function: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> inspect.BoundArguments:
        bound, dependencies = self.arguments(function, args, kwargs)
        cache = current_dependency_cache()
        if cache is None:
            cache = {}
        active: set[Callable[..., Any]] = set()
        for name, marker, value_type in dependencies:
            bound.arguments[name] = self.resolve_dependency(
                marker, value_type, cache, active
            )
        return bound

    async def ainject(
        self,
        function: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        extra_dependencies: Sequence[DependsClass] = (),
        supplied: inspect.BoundArguments | None = None,
    ) -> inspect.BoundArguments:
        bound, dependencies = self.arguments(function, args, kwargs)
        cache = (
            None
            if supplied is not None or extra_dependencies
            else current_dependency_cache()
        )
        if cache is None:
            cache = {}
        active: set[Callable[..., Any]] = set()
        for name, marker, value_type in dependencies:
            bound.arguments[name] = await self.aresolve_dependency(
                marker, value_type, cache, active, supplied
            )
        for dependency in extra_dependencies:
            await self.aresolve_dependency(
                dependency, None, cache, active, supplied
            )
        return bound

    def __call__[**P, R](self, function: Callable[P, R]) -> Callable[P, R]:
        if inspect.iscoroutinefunction(function):

            @wraps(function)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                async with async_invocation_scope():
                    bound = await self.ainject(function, args, kwargs)
                    return await function(*bound.args, **bound.kwargs)

            return cast(Callable[P, R], async_wrapper)

        @wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with invocation_scope():
                bound = self.inject(function, args, kwargs)
                return function(*bound.args, **bound.kwargs)

        return wrapper


inject_depends: DependencyInjector = DependencyInjector()
