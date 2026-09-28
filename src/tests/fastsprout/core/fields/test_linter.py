import pytest

DTO = """
from fastsprout.core import Field

class UserDTO:
    id: Field[int]

reveal_type(UserDTO.id.orm)
"""

BASE_SCHEMA = """
from fastsprout.core import BaseSchema, Field

class UserSchema(BaseSchema):
    field_int: Field[int]

reveal_type(UserSchema.field_int.orm)
"""

TYPED_DATACLASS = """
from fastsprout.core import Field, typed_dataclass

@typed_dataclass
class UserData:
    field_int: Field[int]

reveal_type(UserData.field_int.orm)
"""

TYPED_PYD_DATACLASS = """
from fastsprout.core import Field, typed_pyd_dataclass

@typed_pyd_dataclass
class UserPyd:
    field_int: Field[int]

reveal_type(UserPyd.field_int.orm)
"""

ENTITY = """
from typing import Any, Generic, TypeVar
from fastsprout.core import Field
from fastsprout.core.fields.has_orm import HasOrm

T = TypeVar("T")

class FakeOrm(Generic[T]):
    pass

class Hero(HasOrm[FakeOrm[Any]]):
    id: Field[int]
    name: Field[str]

reveal_type(Hero.id.orm)
reveal_type(Hero.name.orm)
"""

SQL_ENTITY = """
from fastsprout.core import Field
from fastsprout.data.backend.sql import SQLEntity

class Hero(SQLEntity[int]):
    id: Field[int]
    name: Field[str]

reveal_type(Hero.id.orm)
reveal_type(Hero.name.orm)
"""

INSTANCE = """
from typing import Any, Generic, TypeVar
from fastsprout.core import Field
from fastsprout.core.fields.has_orm import HasOrm

T = TypeVar("T")

class FakeOrm(Generic[T]):
    pass

class Hero(HasOrm[FakeOrm[Any]]):
    id: Field[int]
    def __init__(self, id: int) -> None:
        self.id = id

reveal_type(Hero(id=1).id)
"""


@pytest.mark.parametrize("tool", ["mypy", "pyright"])
@pytest.mark.parametrize(
    "snippet,expected",
    [
        pytest.param(DTO, {"mypy": ["None"], "pyright": ["None"]}, id="dto"),
        pytest.param(
            BASE_SCHEMA,
            {"mypy": ["None"], "pyright": ["None"]},
            id="base-schema",
        ),
        pytest.param(
            TYPED_DATACLASS,
            {"mypy": ["None"], "pyright": ["None"]},
            id="typed-dataclass",
        ),
        pytest.param(
            TYPED_PYD_DATACLASS,
            {"mypy": ["None"], "pyright": ["None"]},
            id="typed-pyd-dataclass",
        ),
        pytest.param(
            ENTITY,
            {
                "mypy": ["FakeOrm[Any]", "FakeOrm[Any]"],
                "pyright": ["FakeOrm[Any]", "FakeOrm[Any]"],
            },
            id="entity-orm",
        ),
        pytest.param(
            SQL_ENTITY,
            {
                "mypy": ["Mapped[int]", "Mapped[str]"],
                "pyright": ["Mapped[int]", "Mapped[str]"],
            },
            id="sql-entity-orm",
        ),
        pytest.param(
            INSTANCE,
            {"mypy": ["int"], "pyright": ["int"]},
            id="instance-value",
        ),
    ],
)
def test_reveal(reveal_types, tool, snippet, expected):
    types = reveal_types(tool, snippet)
    assert [t.rsplit(".", 1)[-1] for t in types] == expected[tool]
