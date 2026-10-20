# 2. PostgreSQL

<!-- example-source: examples/testing/02_data/02_postgresql.py -->

Run the same DataR operations against PostgreSQL in a disposable container.

Run this example with Docker using pytest -m integration.
TestPostgreSQL reuses the SQL context's table, session, and binding lifecycle.
Pass a configured PostgresContainer and engine/session factories for native
configuration; the default image is the public postgres image.

## Source

```python
"""Run the same DataR operations against PostgreSQL in a disposable container.

Run this example with Docker using pytest -m integration.
TestPostgreSQL reuses the SQL context's table, session, and binding lifecycle.
Pass a configured PostgresContainer and engine/session factories for native
configuration; the default image is the public postgres image.
"""

from collections.abc import AsyncIterator

import pytest
from sqlmodel import Field as SQLField

from fastsprout.core import Field, ReadField
from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLEntity, SQLSignpost
from fastsprout.testing.core import given, then, when
from fastsprout.testing.data import TestPostgreSQL, TestSQLDatabase


class Hero(SQLEntity[int]):
    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str]


@given("an isolated PostgreSQL database for heroes")
async def database() -> AsyncIterator[TestSQLDatabase[SQLSignpost]]:
    async with TestPostgreSQL(Hero) as database:
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
```

## Result

```text
No tests selected by -m 'not integration'.
```
