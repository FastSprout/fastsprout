from collections.abc import Sequence
from typing import Annotated, overload

from annotated_types import Ge
from typing_extensions import TypeVar

from fastsprout.core import (
    Depends,
    Schema,
    Undefined,
    UndefinedType,
)
from fastsprout.core.depends import DependsClass
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE
from fastsprout.data.entity import Entitieable
from fastsprout.data.router import DataR
from fastsprout.data.types import Valuable

from ...simple_service import Service
from ..protocols import DataSable
from ..types import DataSOperation, Page, SchemaSetting
from . import commands, configuration, queries

__all__ = ["DataS"]

E = TypeVar("E", bound=Entitieable)
R = TypeVar("R", bound=Valuable | Entitieable, default=E)
C = TypeVar("C", bound=Schema | Entitieable, default=E)
U = TypeVar("U", bound=Schema | Entitieable, default=E)
P = TypeVar("P", bound=Schema | Entitieable, default=E)

CreateSetting = TypeVar(
    "CreateSetting", bound=UndefinedType | None, default=UndefinedType
)


class DataS(Service, DataSable[E, R, C, U, P, CreateSetting]):
    """CRUD actions using the entity or explicitly configured schemas."""

    operations: frozenset[DataSOperation] = configuration.DATAS_OPERATIONS
    chunk_size: Annotated[int, Ge(1)] = DEFAULT_ITERATION_CHUNK_SIZE
    entity: type[E]
    page_schema: type[Page[R]] = Page
    entity_type: type[E]
    read_schema: type[R]
    create_schema: type[C]
    update_schema: type[U]
    patch_schema: type[P]

    @overload
    def __init__(
        self,
        entity: type[E] | None = None,
        *,
        read: SchemaSetting[R] = Undefined,
        create: type[C] | CreateSetting,
        update: SchemaSetting[U] = Undefined,
        patch: SchemaSetting[P] = Undefined,
        page: type[Page[R]] | None = None,
        dependencies: Sequence[DependsClass] | None = None,
        operations: frozenset[DataSOperation] | None = None,
        chunk_size: Annotated[int, Ge(1)] | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        entity: type[E] | None = None,
        *,
        read: SchemaSetting[R] = Undefined,
        create: type[C] | UndefinedType = Undefined,
        update: SchemaSetting[U] = Undefined,
        patch: SchemaSetting[P] = Undefined,
        page: type[Page[R]] | None = None,
        dependencies: Sequence[DependsClass] | None = None,
        operations: frozenset[DataSOperation] | None = None,
        chunk_size: Annotated[int, Ge(1)] | None = None,
    ) -> None: ...

    def __init__(
        self,
        entity: type[E] | None = None,
        *,
        read: SchemaSetting[R] = Undefined,
        create: SchemaSetting[C] = Undefined,
        update: SchemaSetting[U] = Undefined,
        patch: SchemaSetting[P] = Undefined,
        page: type[Page[R]] | None = None,
        dependencies: Sequence[DependsClass] | None = None,
        operations: frozenset[DataSOperation] | None = None,
        chunk_size: Annotated[int, Ge(1)] | None = None,
    ) -> None:
        super().__init__(dependencies=dependencies)
        if chunk_size is not None:
            self.chunk_size = chunk_size
        self.entity = self.source(entity)
        if page is not None:
            self.page_schema = page
        overrides: dict[str, SchemaSetting[R | C | U | P]] = {
            "read_schema": read,
            "create_schema": create,
            "update_schema": update,
            "patch_schema": patch,
        }
        configuration.configure_service(self, overrides, operations)

    def source(self, entity: type[E] | None) -> type[E]:
        if entity is None and not hasattr(self, configuration.ENTITY_ATTRIBUTE):
            raise TypeError("Pass an entity or use DataS[Entity]")
        return self.entity_type if entity is None else entity

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        configuration.inherit_entity(cls, DataS)

    async def create(
        self: "DataS[E, R, C, U, P, UndefinedType]",
        entity: E | C,
        datar: DataR = Depends(),
    ) -> R:
        return await commands.create(self, entity, datar)

    update = commands.update
    patch = commands.patch
    delete = commands.delete

    get = queries.get
    exists = queries.exists
    count = queries.count
    list = queries.list
