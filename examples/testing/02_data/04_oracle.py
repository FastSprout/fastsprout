"""Run DataR operations against Oracle Free with an asynchronous driver.

Run this example with Docker using pytest -m integration. TestOracle
starts an Oracle Free container, prepares the selected tables, and restores
entity bindings on exit. A configured OracleDbContainer selects credentials
and the service; engine and session factories retain native configuration.
Oracle VARCHAR2 columns require an explicit length, set here on the name field.
"""

from collections.abc import AsyncIterator

import pytest
from sqlmodel import Field as SQLField

from fastsprout.core import Field, ReadField
from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLEntity, SQLSignpost
from fastsprout.testing.core import given, then, when
from fastsprout.testing.data import TestOracle, TestSQLDatabase


class Hero(SQLEntity[int]):
    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str] = SQLField(max_length=100)


@given("an isolated Oracle database for heroes")
async def database() -> AsyncIterator[TestSQLDatabase[SQLSignpost]]:
    async with TestOracle(Hero) as database:
        yield database


@when("a hero is created and its transaction is committed")
async def created_hero(database: TestSQLDatabase[SQLSignpost]) -> Hero:
    async with DataR() as datar:
        hero = await datar.ability(Hero).create(Hero(id=1, name="Batman"))
    return hero


@pytest.mark.integration
@then("the committed hero is visible in a new transaction")
async def test_get(created_hero: Hero) -> None:
    async with DataR() as datar:
        hero = await datar.ability(Hero).find_exactly_one(
            datar.ability(Hero).query_for().where(Hero.id.eq(created_hero.id))
        )
        assert hero.name == "Batman"
