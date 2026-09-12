from collections.abc import Callable
from typing import Any, cast
from uuid import UUID, uuid4

import sqlalchemy
from sqlalchemy import Column, func
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import declared_attr
from sqlmodel import Field

from fastsprout.core.types.identificable import IdentificatableType
from fastsprout.data.exceptions import NoPrimaryKeyError

from .entity import SQLEntity

__all__ = ["PrimaryKey", "TableName", "get_primary_key"]


def get_primary_key(
    entity: type[SQLEntity[Any]],
) -> tuple[str, ...]:
    """Get the primary key Python attribute names of a SQLModel model.

    Returns the **attribute** names (e.g. ``"id"``), not the SQL
    column names (e.g. ``"material_profile_id"``).  This is important
    when the model declares ``id: ... = PrimaryKey("custom_col")``.
    """

    if not hasattr(entity, "__table__"):
        raise ValueError(f"{entity.__name__} is not a valid SQLModel model.")

    if not entity.__table__.primary_key.columns:  # pyright: ignore[reportAttributeAccessIssue]
        raise NoPrimaryKeyError(
            f"{entity.__name__} has no primary key defined."
        )

    mapper = sa_inspect(entity)
    col_name_to_attr: dict[str, str] = {
        prop.columns[0].name: prop.key for prop in mapper.column_attrs
    }

    return tuple(
        col_name_to_attr[col.name]
        for col in entity.__table__.primary_key.columns  # pyright: ignore[reportAttributeAccessIssue]
    )


def TableName(table_name: str):  # noqa: N802
    return cast(declared_attr, table_name)


def PrimaryKey[ID: IdentificatableType | UUID](  # noqa: N802
    alias: str,
    *,
    default_factory: Callable[[], ID] = uuid4,
    description="Unique identifier for the entity",
    sa_column: Column[ID] | None = None,
) -> ID:
    return Field(
        default_factory=default_factory,
        description=description,
        sa_column=(
            sa_column
            or Column[UUID](
                sqlalchemy.types.UUID(),
                name=alias,
                key=alias,
                primary_key=True,
                unique=True,
                index=True,
                default=func.gen_random_uuid(),
            )
        ),
    )
