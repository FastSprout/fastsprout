from typing import Any, dataclass_transform

from sqlalchemy.orm import Mapped
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlmodel import Field as SQLPydField
from sqlmodel import SQLModel
from sqlmodel.main import SQLModelMetaclass

from fastsprout.core.fields import Field
from fastsprout.core.fields.has_orm import HasOrm
from fastsprout.core.fields.metaclass import (
    collect_field_names,
    read_annotations,
    unwrap_field_annotations,
)


@dataclass_transform(field_specifiers=(Field, SQLPydField))
class TypedSQLMeta(SQLModelMetaclass):
    """SQLModel metaclass + fastsprout Field installation.

    1. __new__: unwrap Field[T] → T for Pydantic/SQLModel
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
            descriptor: Field[Any] = Field._descriptor(fname, orm_attr)
            descriptor.__set_name__(cls, fname)
            setattr(cls, fname, descriptor)


class BaseSQLEntity(
    HasOrm[Mapped[Any]],
    SQLModel,
    metaclass=TypedSQLMeta,
):
    """SQL entity base. `.orm` exposes SQLAlchemy InstrumentedAttribute.

    With the fastsprout mypy plugin, `Hero.id.orm` is typed as Mapped[int]
    (or whatever T the Field is parametrized with).
    """


def test_base_sql_entity():
    class UserSQLEntity(BaseSQLEntity, table=True):
        field_int: Field[int] = SQLPydField(primary_key=True)
        field_str: Field[str]

    assert UserSQLEntity.field_int.set(1).value == 1
    assert UserSQLEntity.field_int.set(2).value == 2
    assert UserSQLEntity.field_str.set("1").value == "1"
    assert UserSQLEntity.field_str.set("2").value != 2
    assert isinstance(UserSQLEntity.field_str.orm, InstrumentedAttribute)
    assert UserSQLEntity.field_str.orm.key == "field_str"
    assert UserSQLEntity(field_int=1, field_str="none").field_int == 1
    assert UserSQLEntity(field_int=2, field_str="none").field_int == 2
    assert UserSQLEntity(field_int=1, field_str="1").field_str == "1"
    assert UserSQLEntity(field_int=1, field_str="2").field_str != 2
