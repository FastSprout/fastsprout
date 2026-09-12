from types import TracebackType
from typing import (
    Self,
    cast,
    get_type_hints,
)

from fastsprout.core.depends import Depends, DependsClass

from ..protocols import UnitOfWork

__all__ = ["SimpleUnitOfWork"]


def get_attrs_annotations[T, **P](uow: UnitOfWork[T, P]) -> dict[str, type[T]]:
    type_annotations: dict[str, T] = get_type_hints(
        type(uow), include_extras=True
    )
    annotated_repo_depends: dict[str, type[T]] = {}

    annotated_repo_depends.update(
        {
            k: v.__dict__["__origin__"]
            for k, v in type_annotations.items()
            if any(
                isinstance(x, DependsClass)
                for x in v.__dict__.get("__metadata__", [])
            )
        }
    )

    annotated_repo_depends.update(
        {
            k: cast(type[T], type_annotations[k])
            for k in dir(uow)
            if isinstance(getattr(uow, k), DependsClass)
        }
    )
    return annotated_repo_depends


class SimpleUnitOfWork[T, **P](UnitOfWork[T, P]):
    def __init__(self, *args: P.args, **kwargs: P.kwargs):
        self._args = args
        self._kwargs = kwargs
        self.__name_attr__: dict[str, T] = {}

    @property
    def attrs_are_init(self) -> bool:
        return bool(self.__name_attr__)

    def _init_attr(self, class_: type[T]) -> T:
        return class_(*self._args, **self._kwargs)

    def __init_attrs__(self) -> dict[str, T]:
        self.__name_attr__ = {}

        for k, v in get_attrs_annotations(self).items():
            self.__name_attr__[k] = self._init_attr(v)
            setattr(self, k, self.__name_attr__[k])
        return self.__name_attr__

    def __clean_attrs__(self):
        for k in list[str](self.__name_attr__.keys()):
            attr = self.__name_attr__.pop(k)
            setattr(self, k, Depends())
            del attr

    def begin(self):
        if self.attrs_are_init:
            raise RuntimeError(f"{self.__class__.__name__} is already init")

        self.__init_attrs__()

    def close(self):
        if not self.attrs_are_init:
            raise RuntimeError(f"{self.__class__.__name__} is not init")

        self.__clean_attrs__()

    def __enter__(self) -> Self:
        self.begin()
        return self

    async def __aenter__(self):
        self.begin()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ):
        self.close()
