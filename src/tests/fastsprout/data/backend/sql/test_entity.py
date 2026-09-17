import subprocess
import sys
from datetime import datetime
from typing import Any, ClassVar

import pytest

from fastsprout.core import Field, InternalField, ReadField, WriteField

from .base_test_sql_entity import BaseTestSQLEntity
from .conftest import (
    CustomSQLBase,
    CustomSQLMiddle,
    CustomSQLRecord,
    SearchField,
    SortField,
    VisibilitySQLUser,
)


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
        "id": Field,
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
        "id": Field,
        "email": Field,
        "password": WriteField,
        "password_hash": InternalField,
        "created_at": ReadField,
        "last_login": InternalField,
    }

    def test_inherited_internal_default(self, entity: VisibilitySQLUser):
        assert entity.last_login is None


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
