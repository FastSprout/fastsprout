# 1. SQLite

<!-- example-source: examples/testing/02_data/01_sqlite.py -->

Reuse an isolated SQLite database across committed DataR operations.

TestSQLite creates the selected tables and binds their signpost for the context.
It removes the tables and restores previous bindings on exit, including after
an exception. Pass an engine or a session factory for SQLAlchemy configuration.

Pytest runs database, created_hero, and test_get through fixture dependencies.
The database context stays open until the test finishes.

## Source

```python
"""Reuse an isolated SQLite database across committed DataR operations.

TestSQLite creates the selected tables and binds their signpost for the context.
It removes the tables and restores previous bindings on exit, including after
an exception. Pass an engine or a session factory for SQLAlchemy configuration.

Pytest runs database, created_hero, and test_get through fixture dependencies.
The database context stays open until the test finishes.
"""

from collections.abc import AsyncIterator

from sqlmodel import Field as SQLField

from fastsprout.core import Field, ReadField
from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLEntity, SQLSignpost
from fastsprout.testing.core import given, then, when
from fastsprout.testing.data import TestSQLDatabase, TestSQLite


class Hero(SQLEntity[int]):
    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str]


@given("an isolated SQLite database for heroes")
async def database() -> AsyncIterator[TestSQLDatabase[SQLSignpost]]:
    async with TestSQLite(Hero) as database:
        yield database


@when("a hero is created and its transaction is committed")
async def created_hero(database: TestSQLDatabase[SQLSignpost]) -> Hero:
    async with DataR() as datar:
        hero = await datar.ability(Hero).create(Hero(id=1, name="Batman"))
    return hero


@then("the committed hero is visible in a new transaction")
async def test_get(created_hero: Hero) -> None:
    async with DataR() as datar:
        hero = await datar.ability(Hero).find_exactly_one(
            datar.ability(Hero).query_for().where(Hero.id.eq(created_hero.id))
        )
        assert hero.name == "Batman"
```

## Result

```text

examples/testing/02_data/01_sqlite.py::test_get PASSED                   [100%]
```
