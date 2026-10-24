from collections.abc import AsyncIterator
from functools import partial
from pathlib import Path
from subprocess import CompletedProcess

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from fastsprout.data.backend.sql import SQLEntity, SQLSignpost
from fastsprout.data.backend.sql.entity import SQLSource
from fastsprout.testing.core import given, then, when
from fastsprout.testing.data import TestSQLDatabase, TestSQLite
from tests.type_checking import TypeChecker

from .base_test_database import BaseTestSQLDatabase
from .conftest import CRM, ContextRecord, CRMRecord


class TestSQLiteContext(BaseTestSQLDatabase):
    @when("a nested database scope exits normally or with an error")
    async def nested_binding(
        self,
        database: TestSQLDatabase[SQLSignpost],
        fail: bool,
    ) -> tuple[SQLSource, SQLSignpost, ValueError | None]:
        failure = None
        nested = TestSQLite(ContextRecord)
        bound: SQLSource = database.signpost
        try:
            async with nested:
                bound = ContextRecord.__signpost__
                if fail:
                    raise ValueError("body failed")
        except ValueError as error:
            failure = error
        return bound, nested.signpost, failure

    @pytest.mark.parametrize("fail", [False, True])
    @then("nested contexts restore bindings even when the body fails")
    def test_binding(
        self,
        database: TestSQLDatabase[SQLSignpost],
        fail: bool,
        nested_binding: tuple[SQLSource, SQLSignpost, ValueError | None],
    ) -> None:
        bound, nested_source, failure = nested_binding
        assert bound is nested_source
        assert nested_source is not database.signpost
        assert (failure is not None) is fail
        assert ContextRecord.__signpost__ is database.signpost

    @when("a context temporarily replaces an inherited entity binding")
    async def inherited_binding(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> tuple[SQLSignpost, SQLSource]:
        previous = SQLSignpost(async_sessionmaker())
        monkeypatch.setattr(SQLEntity, "__signpost__", previous, raising=False)
        async with TestSQLite(ContextRecord):
            during = ContextRecord.__signpost__
        return previous, during

    @then("an inherited binding is restored without a class override")
    def test_inherited_binding(
        self, inherited_binding: tuple[SQLSignpost, SQLSource]
    ) -> None:
        previous, during = inherited_binding
        assert during is not previous
        assert ContextRecord.__signpost__ is previous
        assert "__signpost__" not in vars(ContextRecord)

    @when("a scoped entity is passed to a context with an incompatible source")
    async def invalid_source(self) -> tuple[TypeError | None, bool]:
        failure = None
        async with TestSQLite(CRMRecord, signpost=CRM) as database:
            try:
                async with TestSQLite(CRMRecord):
                    pass
            except TypeError as error:
                failure = error
            unchanged = CRMRecord.__signpost__ is database.signpost
        return failure, unchanged

    @then("an invalid source leaves the original binding unchanged")
    def test_source(
        self, invalid_source: tuple[TypeError | None, bool]
    ) -> None:
        failure, unchanged = invalid_source
        assert isinstance(failure, TypeError)
        assert "instance of CRM" in str(failure)
        assert unchanged
        assert "__signpost__" not in vars(CRMRecord)

    @given("a caller-owned SQLite engine")
    async def caller_engine(self) -> AsyncIterator[AsyncEngine]:
        engine = create_async_engine("sqlite+aiosqlite://", echo=False)
        try:
            yield engine
        finally:
            await engine.dispose()

    @when("a context uses the caller's engine and session factory")
    async def configured(
        self,
        caller_engine: AsyncEngine,
    ) -> tuple[AsyncEngine, bool]:
        async with TestSQLite(
            ContextRecord,
            engine=caller_engine,
            sessions=partial(
                async_sessionmaker, class_=AsyncSession, expire_on_commit=True
            ),
        ) as database:
            async with database.session() as session:
                return database.engine, session.sync_session.expire_on_commit

    @then("custom options survive and caller-owned engines remain usable")
    async def test_configuration(
        self,
        caller_engine: AsyncEngine,
        configured: tuple[AsyncEngine, bool],
    ) -> None:
        engine, expire_on_commit = configured
        assert engine is caller_engine
        assert expire_on_commit is True
        async with caller_engine.connect() as connection:
            assert await connection.scalar(text("SELECT 1")) == 1
            tables = await connection.run_sync(
                lambda connection: inspect(connection).get_table_names()
            )
            assert ContextRecord.__table__.name not in tables

    @when("an active database context is entered again")
    async def reentry_error(
        self,
        database: TestSQLDatabase[SQLSignpost],
    ) -> RuntimeError | None:
        try:
            await database.__aenter__()
        except RuntimeError as error:
            return error
        return None

    @then("reentering an active context does not disturb its resources")
    def test_reentry(
        self,
        database: TestSQLDatabase[SQLSignpost],
        reentry_error: RuntimeError | None,
    ) -> None:
        assert isinstance(reentry_error, RuntimeError)
        assert "already entered" in str(reentry_error)
        assert ContextRecord.__signpost__ is database.signpost

    @when("the SQLite context client is checked")
    def checked_types(self, type_checker: TypeChecker) -> CompletedProcess[str]:
        return type_checker.run(
            Path(__file__).with_name("contexts_typing.py.txt")
        )

    @then("SQLite factories preserve custom signpost types")
    def test_types(
        self, type_checker: TypeChecker, checked_types: CompletedProcess[str]
    ) -> None:
        type_checker.verify(
            Path(__file__).with_name("contexts_typing.py.txt"), checked_types
        )
