import inspect
from collections.abc import Callable, Sequence
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

__all__ = ["DependencyInjector", "Depends", "DependsClass", "inject_depends"]


if TYPE_CHECKING:

    class DependsClass:
        dependency: Callable[..., Any] | None
        use_cache: bool

        def __init__(
            self,
            dependency: Callable[..., Any] | None = None,
            *,
            use_cache: bool = True,
        ): ...

        def __repr__(self) -> str: ...


else:
    try:
        from fastapi.params import Depends as DependsClass
    except ImportError:

        class DependsClass:
            def __init__(
                self,
                dependency: Callable[..., Any] | None = None,
                *,
                use_cache: bool = True,
            ):
                self.dependency = dependency
                self.use_cache = use_cache

            def __repr__(self) -> str:
                attr = getattr(
                    self.dependency, "__name__", type(self.dependency).__name__
                )
                cache = "" if self.use_cache else ", use_cache=False"
                return f"{self.__class__.__name__}({attr}{cache})"


def Depends(  # noqa: N802
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
    def _marker(
        parameter: inspect.Parameter, annotation: Any
    ) -> tuple[Any, Any]:
        if isinstance(parameter.default, DependsClass):
            return parameter.default, annotation
        if get_origin(annotation) is Annotated:
            value_type, *metadata = get_args(annotation)
            for item in metadata:
                if isinstance(item, DependsClass):
                    return item, value_type
        return None, annotation

    def _provider(self, marker: Any, annotation: Any) -> Callable[..., Any]:
        dependency = marker.dependency or annotation
        if not callable(dependency):
            raise TypeError(
                "Depends() needs a provider or a callable annotation"
            )
        return cast(Callable[..., Any], dependency)

    @staticmethod
    def _enter(
        provider: Callable[..., Any], active: set[Callable[..., Any]]
    ) -> None:
        if provider in active:
            raise RuntimeError(f"Circular dependency: {provider}")
        active.add(provider)

    @staticmethod
    def _call_sync(
        provider: Callable[..., Any], bound: inspect.BoundArguments
    ) -> Any:
        if inspect.iscoroutinefunction(provider):
            raise TypeError("Async dependency needs async inject_depends")
        value = provider(*bound.args, **bound.kwargs)
        if inspect.isawaitable(value):
            if inspect.iscoroutine(value):
                value.close()
            raise TypeError("Async dependency needs async inject_depends")
        return value

    def _arguments(
        self,
        function: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        supplied: inspect.BoundArguments | None = None,
    ) -> tuple[inspect.BoundArguments, list[tuple[str, Any, Any]]]:
        if not inspect.isroutine(function) and not inspect.isclass(function):
            function = function.__call__
        signature = inspect.signature(function)
        annotations = get_type_hints(
            inspect.unwrap(function), include_extras=True
        )
        parameters = [
            parameter.replace(
                annotation=annotations.get(name, parameter.annotation)
            )
            for name, parameter in signature.parameters.items()
        ]
        bound = signature.replace(parameters=parameters).bind_partial(
            *args, **kwargs
        )
        self._bind(bound, supplied)
        dependencies = []
        for name, parameter in signature.parameters.items():
            if name in bound.arguments:
                continue
            marker, value_type = self._marker(
                parameter, annotations.get(name, parameter.annotation)
            )
            if marker is not None:
                dependencies.append((name, marker, value_type))
        return bound, dependencies

    def _bind(
        self,
        bound: inspect.BoundArguments,
        supplied: inspect.BoundArguments | None,
    ) -> None:
        if supplied is None:
            return
        parameters = bound.signature.parameters
        for name in parameters.keys() & supplied.arguments.keys() - {"self"}:
            parameter = parameters[name]
            marker, _ = self._marker(parameter, parameter.annotation)
            if marker is None or marker.dependency is None:
                bound.arguments.setdefault(name, supplied.arguments[name])

    def _resolve(
        self,
        marker: Any,
        annotation: Any,
        cache: dict[Callable[..., Any], Any],
        active: set[Callable[..., Any]],
    ) -> Any:
        provider = self._provider(marker, annotation)
        if marker.use_cache and provider in cache:
            return cache[provider]
        self._enter(provider, active)
        try:
            override = self.dependency_overrides.get(
                provider, self.dependency_providers.get(provider, provider)
            )
            bound, dependencies = self._arguments(override, (), {})
            for name, nested, value_type in dependencies:
                bound.arguments[name] = self._resolve(
                    nested, value_type, cache, active
                )
            value = self._call_sync(override, bound)
            if marker.use_cache:
                cache[provider] = value
            return value
        finally:
            active.remove(provider)

    async def _aresolve(
        self,
        marker: Any,
        annotation: Any,
        cache: dict[Callable[..., Any], Any],
        active: set[Callable[..., Any]],
        supplied: inspect.BoundArguments | None = None,
    ) -> Any:
        provider = self._provider(marker, annotation)
        if marker.use_cache and provider in cache:
            return cache[provider]
        self._enter(provider, active)
        try:
            override = self.dependency_overrides.get(
                provider, self.dependency_providers.get(provider, provider)
            )
            bound, dependencies = self._arguments(override, (), {}, supplied)
            for name, nested, value_type in dependencies:
                bound.arguments[name] = await self._aresolve(
                    nested, value_type, cache, active, supplied
                )
            value = override(*bound.args, **bound.kwargs)
            if inspect.isawaitable(value):
                value = await value
            if marker.use_cache:
                cache[provider] = value
            return value
        finally:
            active.remove(provider)

    def resolve(self, marker: Any, annotation: Any) -> Any:
        return self._resolve(marker, annotation, {}, set())

    async def aresolve(self, marker: Any, annotation: Any) -> Any:
        return await self._aresolve(marker, annotation, {}, set())

    def _inject(
        self,
        function: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> inspect.BoundArguments:
        bound, dependencies = self._arguments(function, args, kwargs)
        cache: dict[Callable[..., Any], Any] = {}
        active: set[Callable[..., Any]] = set()
        for name, marker, value_type in dependencies:
            bound.arguments[name] = self._resolve(
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
        bound, dependencies = self._arguments(function, args, kwargs)
        cache: dict[Callable[..., Any], Any] = {}
        active: set[Callable[..., Any]] = set()
        for name, marker, value_type in dependencies:
            bound.arguments[name] = await self._aresolve(
                marker, value_type, cache, active, supplied
            )
        for dependency in extra_dependencies:
            await self._aresolve(dependency, None, cache, active, supplied)
        return bound

    def __call__[**P, R](self, function: Callable[P, R]) -> Callable[P, R]:
        if inspect.iscoroutinefunction(function):

            @wraps(function)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                bound = await self.ainject(function, args, kwargs)
                return await function(*bound.args, **bound.kwargs)

            return cast(Callable[P, R], async_wrapper)

        @wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            bound = self._inject(function, args, kwargs)
            return function(*bound.args, **bound.kwargs)

        return wrapper


inject_depends = DependencyInjector()
