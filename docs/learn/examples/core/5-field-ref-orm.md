# 5. Field Ref ORM

<!-- example-source: examples/core/05_field_ref_orm.py -->

This example builds a small SQLModel bridge to show what `HasOrm` exposes. A class-level `FieldRef.orm` points to SQLAlchemy's mapped attribute, which can be used in SQL expressions; `.set()` still creates a plain field assignment.

Run from the repository root:

```bash
uv run --extra data-sql python examples/core/05_field_ref_orm.py
```

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


class BaseSQLEntity(HasOrm[Mapped[Any]], SQLModel, metaclass=TypedSQLMeta):
    """SQL entity base. `.orm` exposes SQLAlchemy InstrumentedAttribute."""


class Hero(BaseSQLEntity, table=True):
    id: Field[int] = SQLPydField(primary_key=True)
    name: Field[str]


def main() -> None:
    hero = Hero(id=1, name="SuperMan")
    assert hero.id == 1
    assert hero.name == "SuperMan"

    # Class-level: FieldRef with the SQLAlchemy attribute behind `.orm`.
    orm_attr = Hero.name.orm
    assert isinstance(orm_attr, InstrumentedAttribute)
    assert orm_attr.key == "name"

    # `.set(value)` works the same as on a plain Field.
    print(Hero.name.set("Spider"))


if __name__ == "__main__":
    main()
```

## Result

The assertion checks that `Hero.name.orm` is an `InstrumentedAttribute`. The script prints:

```text
FieldAssignment(name='name', value='Spider')
```
