from fastsprout.core import (
    BaseSchema,
    Field,
    typed_dataclass,
    typed_fields,
    typed_pyd_dataclass,
)


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
