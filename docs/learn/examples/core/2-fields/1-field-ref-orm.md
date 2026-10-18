# 1. Field Ref ORM

<!-- example-source: examples/core/02_fields/01_field_ref_orm.py -->

HasOrm + FieldRef.orm with SQLModel.

Requires `sqlmodel` (already in the dev extras).

`Hero.id.orm` returns the SQLAlchemy `InstrumentedAttribute` at runtime.
The Field overload types it as `Mapped[int]` in stock mypy and pyright.
Custom wrappers retain the type arguments declared in HasOrm; for example,
HasOrm[CustomOrm[Any]] exposes CustomOrm[Any] for every field.

## Source

```python
"""HasOrm + FieldRef.orm with SQLModel.

Requires `sqlmodel` (already in the dev extras).

`Hero.id.orm` returns the SQLAlchemy `InstrumentedAttribute` at runtime.
The Field overload types it as `Mapped[int]` in stock mypy and pyright.
Custom wrappers retain the type arguments declared in HasOrm; for example,
HasOrm[CustomOrm[Any]] exposes CustomOrm[Any] for every field.
"""

from typing import Any, dataclass_transform

from sqlalchemy.orm import Mapped
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
            descriptor: Field[Any] = Field.descriptor(fname, orm_attr)
            descriptor.__set_name__(cls, fname)
            setattr(cls, fname, descriptor)


class BaseSQLEntity(HasOrm[Mapped[Any]], SQLModel, metaclass=TypedSQLMeta):
    """SQL entity base. `.orm` exposes SQLAlchemy InstrumentedAttribute."""


class Hero(BaseSQLEntity, table=True):
    id: Field[int] = SQLPydField(primary_key=True)
    name: Field[str]


def main() -> None:
    hero = Hero(id=1, name="SuperMan")
    print(hero.name)

    # Class-level: FieldRef with the SQLAlchemy attribute behind `.orm`.
    orm_attr = Hero.name.orm
    print(orm_attr)

    # `.set(value)` works the same as on a plain Field.
    print(Hero.name.set("Spider"))


if __name__ == "__main__":
    main()
```

## Result

```text
SuperMan
Hero.name
FieldAssignment(name='name', value='Spider')
```
