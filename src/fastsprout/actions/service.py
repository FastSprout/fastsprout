"""Group typed actions and resolve their dependencies."""

import inspect
from collections.abc import Sequence
from typing import ClassVar, Self, get_type_hints, overload

from fastsprout.core.action import BaseActionGroup
from fastsprout.core.depends import DependsClass, inject_depends
from fastsprout.core.depends.invocation import with_dependencies

from .action import FunctionAction

__all__ = ["Service", "decorate_service"]


class ServiceDependency[T]:
    def __init__(self, marker: DependsClass, annotation: type[T]) -> None:
        self.marker = marker
        self.annotation = annotation

    @overload
    def __get__[Owner](self, instance: None, owner: type[Owner]) -> Self: ...

    @overload
    def __get__[Owner](self, instance: Owner, owner: type[Owner]) -> T: ...

    def __get__[Owner](
        self, instance: Owner | None, owner: type[Owner]
    ) -> Self | T:
        if instance is None:
            return self
        return inject_depends.resolve(self.marker, self.annotation)


def decorate_service[T](service: type[T]) -> type[T]:
    type.__setattr__(service, "__action_group__", True)
    annotations = get_type_hints(service)
    for name, member in vars(service).items():
        if isinstance(member, DependsClass):
            setattr(
                service,
                name,
                ServiceDependency(member, annotations[name]),
            )
            continue
        if name.startswith("_") or not inspect.iscoroutinefunction(member):
            continue
        first = next(iter(inspect.signature(member).parameters), None)
        wrapped = (
            with_dependencies(member)
            if first == "self" and not inspect.ismethod(member)
            else FunctionAction(member)
        )
        setattr(service, name, wrapped)
    return service


class Service(BaseActionGroup):
    __action_group__: ClassVar[bool] = True
    dependencies: Sequence[DependsClass] = ()

    def __init__(
        self, *, dependencies: Sequence[DependsClass] | None = None
    ) -> None:
        if dependencies is not None:
            self.dependencies = dependencies

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        decorate_service(cls)
