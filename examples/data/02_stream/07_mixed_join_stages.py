"""Continue a SQL query join with a stream join across two databases.

Customer and Order share a signpost: SQLQuery.join executes their join in
SQL. Country lives in another database, so it joins the resulting stream
through Python key functions. Both stages use one DataR context and start
reading only when iterated. The stream join indexes its right-hand source
in memory, then streams the left-hand rows.

SQLQuery infers the source type; source=sales_source pins its runtime instance.
It rejects Country in this SQL join because Country belongs to Geography;
joining its stream after the SQL stage remains allowed.
The typed bind calls also reject assigning a Geography entity to Sales.
"""

import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLField

from fastsprout.core import Field, ReadField
from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLEntity, SQLQuery, SQLSignpost


class Sales(SQLSignpost): ...


class Geography(SQLSignpost): ...


class Customer(SQLEntity[int, Sales]):
    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str]
    country_id: Field[int]
    active: Field[bool] = Field(default=True)


class Order(SQLEntity[int, Sales]):
    id: ReadField[int] = SQLField(primary_key=True)
    customer_id: Field[int]


class Country(SQLEntity[int, Geography]):
    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str]


async def main() -> None:
    sales_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    geography_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with sales_engine.begin() as connection:
            for entity in (Customer, Order):
                await connection.run_sync(entity.__table__.create)
        async with geography_engine.begin() as connection:
            await connection.run_sync(Country.__table__.create)

        sales = async_sessionmaker(sales_engine, expire_on_commit=False)
        geography = async_sessionmaker(geography_engine, expire_on_commit=False)
        sales_source = Sales(sales)
        geography_source = Geography(geography)
        sales_source.bind(Customer)
        sales_source.bind(Order)
        geography_source.bind(Country)

        async with sales() as session:
            session.add_all(
                [
                    Customer(id=1, name="Ada", country_id=10),
                    Customer(id=2, name="Lin", country_id=20),
                    Customer(id=3, name="Grace", country_id=10, active=False),
                    Order(id=100, customer_id=1),
                    Order(id=101, customer_id=2),
                    Order(id=102, customer_id=3),
                ]
            )
            await session.commit()
        async with geography() as session:
            session.add_all(
                [Country(id=10, name="Poland"), Country(id=20, name="Germany")]
            )
            await session.commit()

        customers = SQLQuery(Customer, source=sales_source).where(
            Customer.active.eq(True)
        )
        orders = customers.join(Order, Customer.id == Order.customer_id)
        orders.order_by(Customer.id)

        async with DataR() as datar:
            sales_rows = datar.stream(orders)
            countries = datar.stream(SQLQuery(Country, source=geography_source))
            combined = sales_rows.join(
                countries,
                on=(lambda row: row[0].country_id, lambda country: country.id),
            )
            async for customer, order, country in combined:
                print(f"Order {order.id}: {customer.name}, {country.name}")
    finally:
        await geography_engine.dispose()
        await sales_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
