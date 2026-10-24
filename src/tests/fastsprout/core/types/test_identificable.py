from uuid import UUID

import pytest
from pydantic import TypeAdapter, ValidationError

from fastsprout.core.types.identificable import IdentificatableType
from fastsprout.testing.core import given, then, when


class TestIdentifiers:
    @given("the public identifier validator")
    def adapter(self) -> TypeAdapter[IdentificatableType]:
        return TypeAdapter(IdentificatableType)

    @when("a value is validated as an identifier")
    def validated(
        self,
        adapter: TypeAdapter[IdentificatableType],
        value: str | int | UUID | list[int] | None,
    ) -> IdentificatableType | ValidationError:
        try:
            return adapter.validate_python(value)
        except ValidationError as error:
            return error

    @pytest.mark.parametrize("value", ["key", 1, UUID(int=1)])
    @then("supported identifiers preserve their values")
    def test_identifiers(
        self,
        validated: IdentificatableType | ValidationError,
        value: str | int | UUID,
    ) -> None:
        assert validated == value

    @pytest.mark.parametrize("value", [None, []])
    @then("null and unhashable identifiers are rejected")
    def test_invalid_identifiers(
        self, validated: IdentificatableType | ValidationError
    ) -> None:
        assert isinstance(validated, ValidationError)
        assert "Identificatable protocol" in str(validated)

    @when("a JSON schema is generated for identifiers")
    def json_schema(
        self, adapter: TypeAdapter[IdentificatableType]
    ) -> dict[str, str]:
        return adapter.json_schema()

    @then("identifier schemas describe a string identifier contract")
    def test_json_schema(self, json_schema: dict[str, str]) -> None:
        assert json_schema["type"] == "string"
        assert "Identificatable" in json_schema["description"]
