from uuid import UUID, uuid4

import pytest

from fastsprout.core import BaseSchema, Field


class Hero(BaseSchema):
    name: Field[str]
    age: Field[int] = Field(default=0)
    uid: Field[UUID] = Field(default_factory=uuid4)


def test_default_value_applied() -> None:
    assert Hero(name="SuperMan").age == 0


def test_default_value_overridden() -> None:
    assert Hero(name="Batman", age=42).age == 42


def test_default_factory_applied_per_instance() -> None:
    first, second = Hero(name="A"), Hero(name="B")
    assert isinstance(first.uid, UUID)
    assert first.uid != second.uid


def test_factory_used_not_literal() -> None:
    assert Hero(name="A", uid=uuid4()).uid != uuid4()


def test_required_field_has_no_default() -> None:
    with pytest.raises(Exception):  # noqa: B017
        Hero()


def test_dump_uses_defaults() -> None:
    payload = Hero(name="SuperMan").model_dump(by_alias=True)
    assert payload["age"] == 0
    assert "uid" in payload


class Villain(BaseSchema):
    name: Field[str]
    level: Field[int] = (
        0  # raw literal — works at runtime too  # pyright: ignore[reportAssignmentType]
    )


def test_raw_literal_default() -> None:
    assert Villain(name="Joker").level == 0
    assert Villain(name="Joker", level=9).level == 9
