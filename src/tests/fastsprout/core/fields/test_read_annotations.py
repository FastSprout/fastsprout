from types import GenericAlias
from typing import TypeAliasType

from fastsprout.core import Field
from fastsprout.core.fields.metaclass import (
    collect_field_names,
    read_annotations,
)
from fastsprout.testing.core import given, then, when

type Alias[T] = Field[T]


class TestFieldAlias:
    @given("a parameterized alias of a FastSprout field")
    def annotation(self) -> TypeAliasType:
        return Alias

    @when("field names are collected from aliased and ordinary annotations")
    def names(self, annotation: TypeAliasType) -> list[str]:
        return collect_field_names(
            {"value": GenericAlias(annotation, int), "label": str}
        )

    @then("the alias is recognized without treating ordinary types as fields")
    def test_alias(self, names: list[str]) -> None:
        assert names == ["value"]


def test_returns_annotations_dict_when_present():
    ns = {"__annotations__": {"x": int, "y": str}}
    assert read_annotations(ns) == {"x": int, "y": str}


def test_falls_back_to_annotate_func_pep749():
    def annotate(fmt: int) -> dict[str, type]:
        return {"x": int}

    ns = {"__annotate_func__": annotate}
    assert read_annotations(ns) == {"x": int}


def test_falls_back_to_annotate_attribute():
    def annotate(fmt: int) -> dict[str, type]:
        return {"y": str}

    ns = {"__annotate__": annotate}
    assert read_annotations(ns) == {"y": str}


def test_swallows_annotate_func_exceptions():
    def annotate(fmt: int) -> dict[str, type]:
        raise NameError("forward ref not resolvable yet")

    ns = {"__annotate_func__": annotate}
    assert read_annotations(ns) == {}


def test_returns_empty_when_nothing_present():
    assert read_annotations({}) == {}
