from typing import Any, Generic, Protocol, TypeVar, dataclass_transform

from sqlalchemy import MetaData
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import registry as sa_registry
from sqlmodel import Field as SQLPydField
from sqlmodel import SQLModel
from sqlmodel.main import SQLModelMetaclass

from fastsprout.core import Field
from fastsprout.core.fields.field import model_building_context_var
from fastsprout.core.fields.has_orm import HasOrm
from fastsprout.core.fields.metaclass import (
    collect_field_names,
    read_annotations,
    unwrap_field_annotations,
)
from fastsprout.core.types import IdentificatorType
from fastsprout.data.entity import Entitieable

__all__ = ["SQL_ENTITY_REGISTRY", "SQLEntity", "SoftDeletableSQLEntity"]

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


@dataclass_transform(field_specifiers=(Field, SQLPydField))
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
        field_names = collect_field_names(annotations)
        unwrap_field_annotations(annotations, namespace)

        for fname in field_names:
            if isinstance(annotations.get(fname), TypeVar):
                annotations[fname] = Any
        namespace["__fastsprout_fields__"] = field_names
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
        else:
            targets = cls.__dict__.get("__fastsprout_fields__", [])
        for fname in targets:
            orm_attr = (
                getattr(cls, fname, None) if hasattr(cls, "__table__") else None
            )
            descriptor: Field[Any] = Field(fname, orm=orm_attr)
            descriptor.__set_name__(cls, fname)
            setattr(cls, fname, descriptor)


class SQLEntity(
    SQLModel,
    HasOrm[Mapped[Any]],
    Entitieable[IDT],
    Generic[IDT],  # noqa: UP046  # SQLModel/pydantic can't build multi-level PEP 695 generics
    metaclass=TypedSQLMeta,
    registry=SQL_ENTITY_REGISTRY,
):
    id: Field[IDT]


class SoftDeletableSQLEntity(SQLEntity[IDT], Generic[IDT], table=False):  # noqa: UP046
    remove: Field[bool] = SQLPydField(default=False)
