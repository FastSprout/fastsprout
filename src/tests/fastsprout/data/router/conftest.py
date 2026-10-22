from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import Field as SQLField

from fastsprout.core import Field, ReadField
from fastsprout.data.backend.sql import SQLEntity, SQLSignpost
from fastsprout.testing.core import given
from fastsprout.testing.data import TestSQLite


class Item(SQLEntity[int]):
    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str] = Field(default="")


@given("an isolated SQLite database for DataR operations")
async def signpost() -> AsyncIterator[SQLSignpost]:
    async with TestSQLite(Item) as database:
        yield database.signpost


class JoinOrder(SQLEntity[int]):
    id: ReadField[int] = SQLField(primary_key=True)
    customer_id: Field[int]
    product_id: Field[int]


class JoinCustomer(SQLEntity[int]):
    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str]


class JoinProduct(SQLEntity[int]):
    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str]


@given("orders and their catalog stored in two isolated SQLite databases")
async def databases() -> AsyncIterator[tuple[AsyncEngine, AsyncEngine]]:
    async with (
        TestSQLite(JoinOrder) as orders,
        TestSQLite(JoinCustomer, JoinProduct) as catalog,
    ):
        async with orders.session() as session:
            session.add_all(
                [
                    JoinOrder(id=1, customer_id=10, product_id=20),
                    JoinOrder(id=2, customer_id=11, product_id=21),
                    JoinOrder(id=3, customer_id=99, product_id=20),
                ]
            )
            await session.commit()
        async with catalog.session() as session:
            session.add_all(
                [
                    JoinCustomer(id=10, name="Ada"),
                    JoinCustomer(id=11, name="Lin"),
                    JoinProduct(id=20, name="Tea"),
                    JoinProduct(id=21, name="Coffee"),
                ]
            )
            await session.commit()
        yield orders.engine, catalog.engine
