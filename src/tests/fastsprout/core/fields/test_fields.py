from typing_extensions import TypeForm

from fastsprout.core import (
    BaseSchema,
    Field,
    typed_dataclass,
    typed_fields,
    typed_pyd_dataclass,
)
from fastsprout.core.fields.field_assigment import FieldAssignment
from fastsprout.core.fields.field_ref import FieldRef
from fastsprout.testing.core import given, then, when


class LockedAnnotations(type):
    def __setattr__(
        cls, name: str, value: Field[str] | dict[str, TypeForm[Field[str]]]
    ) -> None:
        if name == "__annotations__":
            raise AttributeError("Annotations are immutable")
        super().__setattr__(name, value)


class TestLockedAnnotations:
    @when("typed fields are installed on a class with immutable annotations")
    def installed(self) -> str:
        @typed_fields
        class LockedFields(metaclass=LockedAnnotations):
            value: Field[str] = Field(default="available")

        return LockedFields().value

    @then("descriptors work even when the metaclass cannot rewrite annotations")
    def test_descriptors(self, installed: str) -> None:
        assert installed == "available"


def test_base_schema():
    class UserSchema(BaseSchema):
        field_int: Field[int]
        field_str: Field[str]

    assert UserSchema.field_int.set(1).value == 1
    assert UserSchema.field_int.set(2).value == 2
    assert UserSchema.field_str.set("1").value == "1"
    assert UserSchema.field_str.set("2").value != 2
    assert UserSchema.field_str.orm is None
    assert UserSchema(field_int=1, field_str="none").field_int == 1
    assert UserSchema(field_int=2, field_str="none").field_int == 2
    assert UserSchema(field_int=1, field_str="1").field_str == "1"
    assert UserSchema(field_int=1, field_str="2").field_str != 2


def test_typed_dataclass():
    @typed_dataclass
    class UserDataClass:
        field_int: Field[int]
        field_str: Field[str]

    assert UserDataClass.field_int.set(1).value == 1
    assert UserDataClass.field_int.set(2).value == 2
    assert UserDataClass.field_str.set("1").value == "1"
    assert UserDataClass.field_str.set("2").value != 2
    assert UserDataClass.field_str.orm is None
    assert UserDataClass(field_int=1, field_str="none").field_int == 1
    assert UserDataClass(field_int=2, field_str="none").field_int == 2
    assert UserDataClass(field_int=1, field_str="1").field_str == "1"
    assert UserDataClass(field_int=1, field_str="2").field_str != 2


def test_typed_pydantic_dataclass():
    @typed_pyd_dataclass
    class UserPydDataClass:
        field_int: Field[int]
        field_str: Field[str]

    assert UserPydDataClass.field_int.set(1).value == 1
    assert UserPydDataClass.field_int.set(2).value == 2
    assert UserPydDataClass.field_str.set("1").value == "1"
    assert UserPydDataClass.field_str.set("2").value != 2
    assert UserPydDataClass.field_str.orm is None
    assert UserPydDataClass(field_int=1, field_str="none").field_int == 1
    assert UserPydDataClass(field_int=2, field_str="none").field_int == 2
    assert UserPydDataClass(field_int=1, field_str="1").field_str == "1"
    assert UserPydDataClass(field_int=1, field_str="2").field_str != 2


def test_typed_fields():
    @typed_fields
    class UserFields:
        field_int: Field[int]
        field_str: Field[str]

        def __init__(self, field_int: int, field_str: str) -> None:
            self.field_int = field_int
            self.field_str = field_str

    assert UserFields.field_int.set(1).value == 1
    assert UserFields.field_int.set(2).value == 2
    assert UserFields.field_str.set("1").value == "1"
    assert UserFields.field_str.set("2").value != 2

    assert UserFields(field_int=1, field_str="none").field_int == 1
    assert UserFields(field_int=2, field_str="none").field_int == 2
    assert UserFields(field_int=1, field_str="1").field_str == "1"
    assert UserFields(field_int=1, field_str="2").field_str != 2


class TestFieldAssignment:
    @given("an integer field descriptor")
    def field(self) -> Field[int, BaseSchema]:
        return Field[int, BaseSchema].descriptor("power")

    @given("a typed field assignment")
    def assignment(self, field: Field[int, BaseSchema]) -> FieldAssignment[int]:
        return field.set(10)

    @when("equivalent and distinct assignments are used as set keys")
    def assignments(
        self, assignment: FieldAssignment[int]
    ) -> set[FieldAssignment[int]]:
        return {
            assignment,
            FieldAssignment("power", 10),
            FieldAssignment("power", 20),
        }

    @then("assignment equality and hashing use both the field and its value")
    def test_equality(
        self,
        assignment: FieldAssignment[int],
        assignments: set[FieldAssignment[int]],
    ) -> None:
        assert len(assignments) == 2
        assert assignment == FieldAssignment("power", 10)
        assert assignment != FieldAssignment("age", 10)
        assert assignment != FieldAssignment("power", 20)
        assert assignment.__eq__(10) is NotImplemented
        assert repr(assignment) == "FieldAssignment(name='power', value=10)"

    @when("the field descriptor is represented")
    def represented(self, field: Field[int, BaseSchema]) -> str:
        return repr(field)

    @then("field representations identify their bound name")
    def test_representation(self, represented: str) -> None:
        assert represented == "Field('power')"

    @when("the descriptor is accessed on its owner class")
    def reference(
        self, field: Field[int, BaseSchema]
    ) -> FieldRef[BaseSchema, int, None]:
        return field.__get__(None, BaseSchema)

    @then("the field reference identifies its owner and field")
    def test_reference(
        self, reference: FieldRef[BaseSchema, int, None]
    ) -> None:
        assert repr(reference) == "<BaseSchema.power>"

    @given("a descriptor bound to a named storage column")
    def storage_field(self) -> Field[int, BaseSchema, str]:
        return Field[int, BaseSchema, str].descriptor("power", "hero_power")

    @when("the storage descriptor is accessed on its owner")
    def storage_reference(
        self, storage_field: Field[int, BaseSchema, str]
    ) -> FieldRef[BaseSchema, int, str | None]:
        return storage_field.__get__(None, BaseSchema)

    @then("the reference preserves the adapter's column binding")
    def test_storage_reference(
        self, storage_reference: FieldRef[BaseSchema, int, str | None]
    ) -> None:
        assert storage_reference.orm == "hero_power"
