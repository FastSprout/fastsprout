from typing import Any, dataclass_transform

from sqlalchemy.orm import Mapped
from sqlmodel import Field as SQLPydField
from sqlmodel import SQLModel
from sqlmodel.main import SQLModelMetaclass

from fastsprout.core import Field
from fastsprout.core.fields.has_orm import HasOrm
from fastsprout.core.fields.metaclass import (
    collect_field_names,
    read_annotations,
    unwrap_field_annotations,
)
from fastsprout.core.types import IdentificatorType
from fastsprout.data.entity import Entitieable

__all__ = ["SQLEntity", "SoftDeletableSQLEntity"]


@dataclass_transform(field_specifiers=(Field, SQLPydField))
class TypedSQLMeta(SQLModelMetaclass):
    """SQLModel metaclass + fastsprout Field installation.

    1. __new__: unwrap SQLField[T] → T for Pydantic/SQLModel
    2. __init__: capture SA InstrumentedAttribute and install Field carrying it
    """

    def __new__(mcs, name, bases, namespace, **kwargs):
        annotations = read_annotations(namespace)
        field_names = collect_field_names(annotations)
        unwrap_field_annotations(annotations, namespace)
        namespace["__fastsprout_fields__"] = field_names
        return super().__new__(mcs, name, bases, namespace, **kwargs)

    def __init__(cls, name, bases, namespace, **kwargs):  # noqa: N805
        super().__init__(name, bases, namespace, **kwargs)
        if not hasattr(cls, "__table__"):
            return
        for fname in getattr(cls, "__fastsprout_fields__", []):
            orm_attr = getattr(cls, fname, None)
            descriptor: Field[Any] = Field(fname, orm=orm_attr)
            descriptor.__set_name__(cls, fname)
            setattr(cls, fname, descriptor)


class SQLEntity[ID: IdentificatorType](
    SQLModel,
    HasOrm[Mapped[Any]],
    Entitieable[ID],
    metaclass=TypedSQLMeta,
): ...


class SoftDeletableSQLEntity[ID: IdentificatorType](SQLEntity[ID]):
    remove: Field[bool] = SQLPydField(default=False)
