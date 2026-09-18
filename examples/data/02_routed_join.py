"""Join entities from two separate databases through their signposts."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import assert_type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLField

from fastsprout.core import Field
from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLEntity, SQLQuery
from fastsprout.data.backend.sql.entity import SQLSignpost


class Order(SQLEntity[int]):
    id: Field[int] = SQLField(primary_key=True)
    customer_id: Field[int]


class Customer(SQLEntity[int]):
    id: Field[int] = SQLField(primary_key=True)
    name: Field[str]


@asynccontextmanager
async def database[E: SQLEntity[int]](
    entity: type[E], rows: list[E]
) -> AsyncIterator[None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as connection:
            await connection.run_sync(entity.__table__.create)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        entity.__signpost__ = SQLSignpost(factory)
        async with factory() as session:
            session.add_all(rows)
            await session.commit()
        yield
    finally:
        await engine.dispose()


async def main() -> None:
    async with (
        database(
            Order, [Order(id=1, customer_id=10), Order(id=2, customer_id=11)]
        ),
        database(
            Customer, [Customer(id=10, name="Ada"), Customer(id=11, name="Lin")]
        ),
        DataR() as data,
    ):
        # Join accepts the same queries as DataR.stream.
        orders = data.join(SQLQuery(entity=Order))
        everyone = orders.join(
            SQLQuery(entity=Customer),
            on=(lambda row: row[0].customer_id, lambda customer: customer.id),
        )
        # A query can restrict one source before the in-memory join.
        only_ada = orders.join(
            SQLQuery(
                entity=Customer,
                statement=select(Customer).where(Customer.name.orm == "Ada"),
            ),
            on=(lambda row: row[0].customer_id, lambda customer: customer.id),
        )

        rows = await only_ada.to_list()
        assert_type(rows, list[tuple[Order, Customer]])
        assert [(order.id, customer.name) for order, customer in rows] == [
            (1, "Ada")
        ]
        print([(order.id, customer.name) for order, customer in rows])

        # Branching does not change the earlier plan. Consume within DataR.
        result = [
            (order.id, customer.name) async for order, customer in everyone
        ]
        assert result == [(1, "Ada"), (2, "Lin")]
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
