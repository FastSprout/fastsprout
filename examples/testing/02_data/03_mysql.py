"""Run one reusable test against MySQL and MariaDB containers.

Run both cases with Docker using pytest -m integration. The contexts
share SQL table setup, signpost binding, and cleanup. Pass a configured
MySqlContainer or engine/session factories to change native settings.
"""

from collections.abc import AsyncIterator

import pytest
from sqlmodel import Field as SQLField

from fastsprout.core import Field, ReadField
from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLEntity, SQLSignpost
from fastsprout.testing.core import given, then, when
from fastsprout.testing.data import TestMariaDB, TestMySQL, TestSQLDatabase


class Hero(SQLEntity[int]):
    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str]


@given("an isolated MySQL or MariaDB database")
async def database(
    backend: str,
) -> AsyncIterator[TestSQLDatabase[SQLSignpost]]:
    context = TestMySQL(Hero) if backend == "mysql" else TestMariaDB(Hero)
    async with context as database:
        yield database


@when("a hero is created and its transaction is committed")
async def created_hero(database: TestSQLDatabase[SQLSignpost]) -> Hero:
    async with DataR() as datar:
        hero = await datar.ability(Hero).create(Hero(id=1, name="Batman"))
    return hero


@pytest.mark.integration
@pytest.mark.parametrize("backend", ["mysql", "mariadb"])
@then("the same DataR code persists a hero on either server")
async def test_mysql(created_hero: Hero) -> None:
    async with DataR() as datar:
        hero = await datar.ability(Hero).find_exactly_one(
            datar.ability(Hero).query_for().where(Hero.id.eq(created_hero.id))
        )
        assert hero.name == "Batman"
