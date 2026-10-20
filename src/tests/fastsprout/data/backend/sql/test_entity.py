import subprocess
import sys
from datetime import datetime
from typing import ClassVar
from uuid import uuid4

import pytest

from fastsprout.core import (
    Field,
    InternalField,
    ReadField,
    WriteDTO,
    WriteField,
)
from fastsprout.testing.core import then, when

from .base_test_sql_entity import BaseTestSQLEntity, SQLTestField
from .conftest import (
    CustomSQLBase,
    CustomSQLMiddle,
    CustomSQLRecord,
    SearchField,
    SortField,
    VisibilitySQLUser,
)


class VisibilitySQLUserCreate(WriteDTO, VisibilitySQLUser): ...


class TestCustomSQLFields(BaseTestSQLEntity[CustomSQLRecord]):
    entity_type = CustomSQLRecord
    data: ClassVar[dict[str, str | datetime]] = {
        "code": "a",
        "sort_key": "01",
        "inherited": "base",
        "name": "first",
    }
    updated_data: ClassVar[dict[str, str]] = {"code": "updated"}
    field_types: ClassVar[dict[str, type[SQLTestField]]] = {
        "id": ReadField,
        "code": SearchField,
        "sort_key": SortField,
        "inherited": SearchField,
        "name": SearchField,
    }

    @when("an unmapped base descriptor is inspected")
    def descriptor_matches(
        self,
        entity_type: type[CustomSQLBase],
        name: str,
        field_type: type[SearchField[str] | SortField[str]],
    ) -> bool:
        return type(vars(entity_type)[name]) is field_type

    @pytest.mark.parametrize(
        "entity_type, name, field_type",
        [
            (CustomSQLBase, "code", SearchField),
            (CustomSQLMiddle, "sort_key", SortField),
        ],
    )
    @then("unmapped inheritance preserves custom descriptor classes")
    def test_unmapped_bases_preserve_descriptors(
        self, descriptor_matches: bool
    ) -> None:
        assert descriptor_matches


class TestSQLVisibilityFields(BaseTestSQLEntity[VisibilitySQLUser]):
    entity_type = VisibilitySQLUser
    data: ClassVar[dict[str, str | datetime]] = {
        "email": "a@b.c",
        "password": "secret",
        "password_hash": "hash",
        "created_at": datetime(2026, 9, 17),
    }
    updated_data: ClassVar[dict[str, str]] = {"password_hash": "updated-hash"}
    field_types: ClassVar[dict[str, type[SQLTestField]]] = {
        "id": ReadField,
        "email": Field,
        "password": WriteField,
        "password_hash": InternalField,
        "created_at": ReadField,
        "last_login": InternalField,
    }

    @then("the inherited internal default remains None")
    def test_inherited_internal_default(
        self, entity: VisibilitySQLUser
    ) -> None:
        assert entity.last_login is None


class TestSQLCreateDTO:
    @when("a write DTO is constructed without the generated identity")
    def user(self) -> VisibilitySQLUserCreate:
        return VisibilitySQLUserCreate(email="a@b.c", password="secret")

    @when("the generated identity is accessed or supplied explicitly")
    def identity_errors(
        self, user: VisibilitySQLUserCreate
    ) -> list[AttributeError]:
        errors: list[AttributeError] = []
        try:
            user.__getattribute__("id")
        except AttributeError as error:
            errors.append(error)
        try:
            VisibilitySQLUserCreate(
                id=uuid4(), email="a@b.c", password="secret"
            )
        except AttributeError as error:
            errors.append(error)
        return errors

    @then("write DTOs exclude generated identities and reject explicit access")
    def test_create_dto_excludes_generated_identity(
        self,
        user: VisibilitySQLUserCreate,
        identity_errors: list[AttributeError],
    ) -> None:
        assert "id" not in vars(user)
        assert len(identity_errors) == 2
        assert all("not accessible" in str(error) for error in identity_errors)


class TestSQLImports:
    @when("SQL is imported by a fresh interpreter")
    def imported(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-c",
                "from fastsprout.data.backend.sql import SQLEntity",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    @then("the SQL import succeeds without prior initialization")
    def test_sql_can_be_imported_in_a_fresh_interpreter(
        self, imported: subprocess.CompletedProcess[str]
    ) -> None:
        assert imported.returncode == 0, imported.stdout + imported.stderr
