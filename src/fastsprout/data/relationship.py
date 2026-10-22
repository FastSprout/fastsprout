"""One-declaration SQL relationships for entity graphs."""

from typing import Any

from sqlmodel import Relationship as SQLRelationship

__all__ = ["Relationship"]


def Relationship() -> Any:  # noqa: N802
    """Declare an entity relation; SQL entities derive its foreign key."""
    relation = SQLRelationship()
    relation.__fastsprout_auto__ = True
    return relation
