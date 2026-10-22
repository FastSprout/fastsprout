from types import GenericAlias

from fastsprout.core import Field, Schema
from fastsprout.core.fields.metaclass import (
    install_descriptors,
    unwrap_field_annotations,
)
from fastsprout.testing.core import given, then, when


class PlainFields(Schema):
    value: Field[int]

    def __init__(self, value: int) -> None:
        self.value = value


class TestFieldMetadata:
    @given("a Field alias with no value argument")
    def annotation(self) -> GenericAlias:
        return GenericAlias(Field, ())

    @when("the field annotation is unwrapped")
    def unwrapped(self, annotation: GenericAlias) -> GenericAlias:
        annotations = {"value": annotation}
        unwrap_field_annotations(annotations)
        return annotations["value"]

    @then("an incomplete alias remains available for subsequent validation")
    def test_incomplete_alias(
        self, annotation: GenericAlias, unwrapped: GenericAlias
    ) -> None:
        assert unwrapped is annotation

    @when("legacy field names are installed twice on a plain schema")
    def installed(self) -> tuple[int, str, bool]:
        install_descriptors(PlainFields, ["value"])
        first = vars(PlainFields)["value"]
        install_descriptors(PlainFields, ["value"])
        return (
            PlainFields(7).value,
            PlainFields.value.name,
            vars(PlainFields)["value"] is first,
        )

    @then("descriptor installation supports names and remains idempotent")
    def test_legacy_names(self, installed: tuple[int, str, bool]) -> None:
        assert installed == (7, "value", True)
