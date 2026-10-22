from uuid import UUID

import pytest
from sqlalchemy import Column, Uuid
from sqlmodel.main import FieldInfo

from fastsprout.data.backend.sql.helpers import PrimaryKey, get_primary_key
from fastsprout.testing.core import given, then, when

from .conftest import CustomSQLBase, Hero, NamedColumnEntity


class TestPrimaryKey:
    @given("a mapped model or an unmapped SQL base")
    def entity(
        self, model: str
    ) -> type[Hero] | type[NamedColumnEntity] | type[CustomSQLBase]:
        models: dict[
            str, type[Hero] | type[NamedColumnEntity] | type[CustomSQLBase]
        ] = {
            "default": Hero,
            "renamed": NamedColumnEntity,
            "unmapped": CustomSQLBase,
        }
        return models[model]

    @when("the model's primary key attribute names are requested")
    def names(
        self, entity: type[Hero] | type[NamedColumnEntity] | type[CustomSQLBase]
    ) -> tuple[str, ...] | ValueError:
        try:
            return get_primary_key(entity)
        except ValueError as error:
            return error

    @pytest.mark.parametrize("model", ["default", "renamed", "unmapped"])
    @then("mapped models expose their keys and unmapped bases are rejected")
    def test_primary_key_names(
        self, names: tuple[str, ...] | ValueError, model: str
    ) -> None:
        if model != "unmapped":
            assert names == ("id",)
        else:
            assert isinstance(names, ValueError)
            assert "not a valid SQLModel model" in str(names)

    @given("an optional custom primary key column")
    def column(self, custom: bool) -> Column[UUID] | None:
        return Column("custom_id", Uuid(), primary_key=True) if custom else None

    @when("a primary key field is created")
    def created(self, column: Column[UUID] | None) -> FieldInfo:
        field = PrimaryKey("record_id", sa_column=column)
        if isinstance(field, FieldInfo):
            return field
        raise TypeError("PrimaryKey must return a native SQL field specifier")

    @pytest.mark.parametrize("custom", [False, True])
    @then("the native field preserves a custom column or creates the default")
    def test_column(
        self, created: FieldInfo, column: Column[UUID] | None
    ) -> None:
        assert isinstance(created, FieldInfo)
        if column is not None:
            assert created.sa_column is column
        else:
            assert isinstance(created.sa_column, Column)
            assert created.sa_column.name == "record_id"
            assert created.sa_column.primary_key
            assert created.sa_column.unique
            assert created.sa_column.index
        assert created.description == "Unique identifier for the entity"
