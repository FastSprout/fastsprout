from dataclasses import FrozenInstanceError
from uuid import UUID, uuid4

import pytest

from fastsprout.core import (
    BaseSchema,
    Field,
    InternalField,
    ReadDTO,
    dataclass,
    typed_dataclass,
    typed_fields,
)


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


def test_dataclass_alias_preserves_frozen_fields_and_defaults() -> None:
    assert dataclass is typed_dataclass

    @dataclass(frozen=True)
    class HeroData:
        name: Field[str]
        level: Field[int] = Field(default=1)

    hero = HeroData("Batman")
    assert hero.name == "Batman"
    assert hero.level == 1
    assert hero == HeroData(name="Batman")
    assert hash(hero) == hash(HeroData("Batman"))
    with pytest.raises(FrozenInstanceError):
        hero.__setattr__("name", "Robin")


def test_dataclass_factory_and_keyword_only_constructor() -> None:
    @dataclass(kw_only=True)
    class Batch:
        name: Field[str]
        items: Field[list[int]] = Field(default_factory=list)

    first, second = Batch(name="first"), Batch(name="second")
    first.items.append(1)
    assert first.items == [1]
    assert second.items == []
    with pytest.raises(TypeError):
        Batch(*["invalid positional argument"])


def test_dataclass_with_empty_options() -> None:
    @dataclass()
    class HeroData:
        name: Field[str]

    assert HeroData("Batman").name == "Batman"


@typed_fields
class HeroPower:
    value: Field[str] = Field(default="Money")
    items: Field[list[int]] = Field(default_factory=list)
    tags: Field[list[str]] = Field(default=["hero"])
    optional: Field[str | None] = Field(default=None)


def test_typed_fields_defaults_without_constructor() -> None:
    power = HeroPower()
    assert power.value == "Money"
    assert power.optional is None
    power.value = "Strength"
    assert power.value == "Strength"


def test_typed_fields_mutable_defaults_are_per_instance() -> None:
    first, second = HeroPower(), HeroPower()
    first.items.append(1)
    first.tags.append("batman")
    assert first.items == [1]
    assert second.items == []
    assert first.tags == ["hero", "batman"]
    assert second.tags == ["hero"]


def test_typed_fields_factory_runs_once_on_first_access() -> None:
    calls = 0

    def factory() -> str:
        nonlocal calls
        calls += 1
        return "Money"

    @typed_fields
    class Power:
        value: Field[str] = Field(default_factory=factory)

    assert Power.value.set("Strength").value == "Strength"
    assert calls == 0
    power = Power()
    assert power.value == "Money"
    assert power.value == "Money"
    assert calls == 1


def test_typed_fields_required_value_still_raises() -> None:
    @typed_fields
    class Required:
        value: Field[str]

    with pytest.raises(AttributeError, match="has no attribute 'value'"):
        _ = Required().value


def test_read_dto_blocks_internal_default_before_factory_runs() -> None:
    calls = 0

    def factory() -> str:
        nonlocal calls
        calls += 1
        return "private"

    class User(BaseSchema):
        name: Field[str]
        secret: InternalField[str] = InternalField(default_factory=factory)

    class UserRead(ReadDTO, User): ...

    read = UserRead(name="Ada")
    with pytest.raises(AttributeError, match="not accessible"):
        read.__getattribute__("secret")
    assert calls == 0
