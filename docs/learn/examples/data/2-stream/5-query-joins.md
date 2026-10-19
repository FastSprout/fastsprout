# 5. Query Joins

<!-- example-source: examples/data/02_stream/05_query_joins.py -->

Read three entities with one SQL query and typed tuple results.

SQLQuery.join adds an INNER JOIN to the SQL statement. All participants
must share one SQLSignpost instance. Building the plan performs no reads;
DataR.stream opens the cursor when iteration starts. Use DataR.join for
entities from different sources.

Python predicates and iterator membership conditions run lazily on the
returned rows, before pagination. The join itself still runs in SQL.

## Source

```python
"""Read three entities with one SQL query and typed tuple results.

SQLQuery.join adds an INNER JOIN to the SQL statement. All participants
must share one SQLSignpost instance. Building the plan performs no reads;
DataR.stream opens the cursor when iteration starts. Use DataR.join for
entities from different sources.

Python predicates and iterator membership conditions run lazily on the
returned rows, before pagination. The join itself still runs in SQL.
"""

import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLField

from fastsprout.core import Field, ReadField
from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLEntity, SQLQuery, SQLSignpost

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
factory = async_sessionmaker(engine, expire_on_commit=False)
backend = SQLSignpost(factory)


class Country(SQLEntity[int]):
    __signpost__ = backend

    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str]


class Customer(SQLEntity[int]):
    __signpost__ = backend

    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str]
    country_id: Field[int]


class Order(SQLEntity[int]):
    __signpost__ = backend

    id: ReadField[int] = SQLField(primary_key=True)
    customer_id: Field[int]


async def main() -> None:
    try:
        async with engine.begin() as connection:
            for entity in (Country, Customer, Order):
                await connection.run_sync(entity.__table__.create)
        async with factory() as session:
            session.add_all(
                [
                    Country(id=1, name="Poland"),
                    Customer(id=10, name="Ada", country_id=1),
                    Order(id=100, customer_id=10),
                ]
            )
            await session.commit()

        query = (
            SQLQuery(Order)
            .join(Customer, Order.customer_id == Customer.id)
            .join(Country, Customer.country_id == Country.id)
            .order_by(Order.id)
        )
        async with DataR() as datar:
            async for order, customer, country in datar.stream(query):
                print(f"Order {order.id}: {customer.name}, {country.name}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
Order 100: Ada, Poland
```
