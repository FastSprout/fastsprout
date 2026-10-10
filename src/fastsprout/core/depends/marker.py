"""Dependency markers compatible with FastAPI when it is installed."""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

__all__ = ["DependsClass"]


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
