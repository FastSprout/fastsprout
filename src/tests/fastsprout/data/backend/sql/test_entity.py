import subprocess
import sys
from datetime import datetime
from typing import Any, ClassVar
from uuid import uuid4

import pytest

from fastsprout.core import (
    Field,
    InternalField,
    ReadField,
    WriteDTO,
    WriteField,
)

from .base_test_sql_entity import BaseTestSQLEntity
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
    _entity_type = CustomSQLRecord
    _data: ClassVar[dict[str, Any]] = {
        "code": "a",
        "sort_key": "01",
        "inherited": "base",
        "name": "first",
    }
    _updated_data: ClassVar[dict[str, Any]] = {"code": "updated"}
    _field_types: ClassVar[dict[str, type[Field[Any, Any]]]] = {
        "id": ReadField,
        "code": SearchField,
        "sort_key": SortField,
        "inherited": SearchField,
        "name": SearchField,
    }

    @pytest.mark.parametrize(
        "entity_type, name, field_type",
        [
            (CustomSQLBase, "code", SearchField),
            (CustomSQLMiddle, "sort_key", SortField),
        ],
    )
    def test_unmapped_bases_preserve_descriptors(
        self, entity_type, name, field_type
    ):
        # when
        descriptor = vars(entity_type)[name]
        # then
        assert type(descriptor) is field_type


class TestSQLVisibilityFields(BaseTestSQLEntity[VisibilitySQLUser]):
    _entity_type = VisibilitySQLUser
    _data: ClassVar[dict[str, Any]] = {
        "email": "a@b.c",
        "password": "secret",
        "password_hash": "hash",
        "created_at": datetime(2026, 9, 17),
    }
    _updated_data: ClassVar[dict[str, Any]] = {"password_hash": "updated-hash"}
    _field_types: ClassVar[dict[str, type[Field[Any, Any]]]] = {
        "id": ReadField,
        "email": Field,
        "password": WriteField,
        "password_hash": InternalField,
        "created_at": ReadField,
        "last_login": InternalField,
    }

    def test_inherited_internal_default(self, entity: VisibilitySQLUser):
        assert entity.last_login is None


def test_create_dto_excludes_generated_identity() -> None:
    user = VisibilitySQLUserCreate(email="a@b.c", password="secret")
    assert "id" not in vars(user)
    with pytest.raises(AttributeError, match="not accessible"):
        user.__getattribute__("id")
    with pytest.raises(AttributeError, match="not accessible"):
        VisibilitySQLUserCreate(id=uuid4(), email="a@b.c", password="secret")


def test_sql_can_be_imported_in_a_fresh_interpreter() -> None:
    # when
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from fastsprout.data.backend.sql import SQLEntity",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    # then
    assert result.returncode == 0, result.stdout + result.stderr
