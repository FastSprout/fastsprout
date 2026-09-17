from contextlib import AbstractAsyncContextManager
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Protocol,
    TypeVar,
    dataclass_transform,
)

from sqlalchemy import MetaData
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import registry as sa_registry
from sqlmodel import Field as SQLPydField
from sqlmodel import SQLModel, Table
from sqlmodel.main import SQLModelMetaclass

from fastsprout.core import Field
from fastsprout.core.fields.field import model_building_context_var
from fastsprout.core.fields.has_orm import HasOrm
from fastsprout.core.fields.metaclass import (
    collect_field_descriptors,
    convert_field_specifiers,
    read_annotations,
    unwrap_field_annotations,
)
from fastsprout.core.types import IdentificatorType
from fastsprout.data.backend.implementation import Signpost
from fastsprout.data.entity import Entitieable

__all__ = [
    "SQL_ENTITY_REGISTRY",
    "SQLEntity",
    "SQLSignpost",
    "SoftDeletableSQLEntity",
]

IDT = TypeVar("IDT", bound=IdentificatorType)

SQL_ENTITY_REGISTRY = sa_registry(metadata=MetaData())


def _mro_field_names(cls: type) -> list[str]:
    """All Field-annotated names declared anywhere in the class's MRO."""
    seen: set[str] = set()
    out: list[str] = []
    for klass in cls.__mro__:
        for fname in klass.__dict__.get("__fastsprout_fields__", ()):
            if fname not in seen:
                seen.add(fname)
                out.append(fname)
    return out


@dataclass_transform(
    kw_only_default=True, field_specifiers=(Field, SQLPydField)
)
class TypedSQLMeta(SQLModelMetaclass, type(Protocol)):
    """SQLModel metaclass + fastsprout Field installation.

    1. __new__: unwrap Field[T] → T for Pydantic/SQLModel
    2. __init__: capture SA InstrumentedAttribute and install Field carrying it
    """

    def __new__(mcs, name, bases, namespace, **kwargs):
        if (
            "table" not in kwargs
            and "__pydantic_generic_metadata__" not in kwargs
            and any(isinstance(b, TypedSQLMeta) for b in bases)
        ):
            kwargs["table"] = True
        annotations = read_annotations(namespace)
        field_descriptors = collect_field_descriptors(annotations)
        field_names = list(field_descriptors)
        unwrap_field_annotations(annotations, namespace)
        convert_field_specifiers(namespace, field_names)

        for fname in field_names:
            if isinstance(annotations.get(fname), TypeVar):
                annotations[fname] = Any
        namespace["__fastsprout_fields__"] = field_names
        namespace["__fastsprout_descriptors__"] = field_descriptors
        token = model_building_context_var.set(True)
        try:
            return super().__new__(mcs, name, bases, namespace, **kwargs)
        finally:
            model_building_context_var.reset(token)

    def __init__(cls, name, bases, namespace, **kwargs):
        super().__init__(name, bases, namespace, **kwargs)
        if hasattr(cls, "__table__"):
            model_fields = getattr(cls, "model_fields", {})
            targets = [n for n in _mro_field_names(cls) if n in model_fields]
            mapper_attrs = sa_inspect(cls).attrs
        else:
            targets = cls.__dict__.get("__fastsprout_fields__", [])
            mapper_attrs = {}
        descriptors = {
            name: descriptor
            for base in reversed(cls.__mro__)
            for name, descriptor in vars(base)
            .get("__fastsprout_descriptors__", {})
            .items()
        }
        for fname in targets:
            orm_attr = (
                mapper_attrs[fname].class_attribute
                if fname in mapper_attrs
                else None
            )
            descriptor: Field[Any] = descriptors.get(fname, Field)._descriptor(
                fname, orm_attr
            )
            descriptor.__set_name__(cls, fname)
            setattr(cls, fname, descriptor)


class SQLSignpost(Signpost[AbstractAsyncContextManager[AsyncSession]]): ...


class SQLEntity(
    SQLModel,
    HasOrm[Mapped[Any]],
    Entitieable[IDT],
    Generic[IDT],  # noqa: UP046  # SQLModel/pydantic can't build multi-level PEP 695 generics
    metaclass=TypedSQLMeta,
    registry=SQL_ENTITY_REGISTRY,
):
    if TYPE_CHECKING:
        __table__: ClassVar[Table]

    __signpost__: ClassVar[SQLSignpost]  # pyright: ignore[reportIncompatibleVariableOverride]

    id: Field[IDT]


class SoftDeletableSQLEntity(SQLEntity[IDT], Generic[IDT], table=False):  # noqa: UP046
    remove: Field[bool] = SQLPydField(default=False)
