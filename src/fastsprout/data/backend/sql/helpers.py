from collections.abc import Callable
from typing import cast
from uuid import UUID, uuid4

import sqlalchemy
from sqlalchemy import Column, func
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import declared_attr
from sqlmodel import Field as SQLModField
from sqlmodel import SQLModel

from fastsprout.core import Field
from fastsprout.core.types.identificable import IdentificatableType

from .entity import SQLEntityClassable, SQLSource

__all__ = ["PrimaryKey", "TableName", "get_primary_key"]


def get_primary_key(
    entity: SQLEntityClassable[SQLModel, SQLSource],
) -> tuple[str, ...]:
    """Get the primary key Python attribute names of a SQLModel model.

    Returns the **attribute** names (e.g. ``"id"``), not the SQL
    column names (e.g. ``"material_profile_id"``). This is important
    when the model declares ``id: ... = PrimaryKey("custom_col")``.
    """
    model = entity.__sql_entity__()
    if not hasattr(model, "__table__"):
        raise ValueError(f"{model.__name__} is not a valid SQLModel model.")

    mapper = sa_inspect(model)
    return tuple(
        mapper.get_property_by_column(column).key
        for column in mapper.primary_key
    )


def TableName(table_name: str) -> declared_attr[str]:  # noqa: N802  # Preserve the public SQL factory naming convention.
    return cast(declared_attr, table_name)


def PrimaryKey[ID: IdentificatableType | UUID](  # noqa: N802  # Preserve the public SQL factory naming convention.
    alias: str,
    *,
    default_factory: Callable[[], ID] = uuid4,
    description: str = "Unique identifier for the entity",
    sa_column: Column[ID] | None = None,
) -> Field[ID]:
    return SQLModField(
        default_factory=default_factory,
        description=description,
        sa_column=(
            sa_column
            if sa_column is not None
            else Column[UUID](
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
