from collections.abc import Callable
from typing import TYPE_CHECKING, Any

__all__ = ["Depends", "DependsClass"]


if TYPE_CHECKING:

    class DependsClass:  # pyright: ignore
        def __init__(
            self,
            dependency: Callable[..., Any] | None = None,
            *,
            use_cache: bool = True,
        ): ...

        def __repr__(self) -> str: ...


try:
    from fastapi.params import (  # type: ignore
        Depends as DependsClass,
    )
except ImportError:

    class DependsClass:  # type: ignore
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
