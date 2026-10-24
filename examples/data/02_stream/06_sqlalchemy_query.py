"""Combine a SQLAlchemy aggregate query with SQLQuery conditions and paging.

Find active customers with at least two paid orders totaling 100 or more.
SQLAlchemy builds a CTE with GROUP BY and HAVING, then joins it to customers.
Use field.orm for SQLAlchemy expressions; field.eq builds our query predicate.

SQLQuery accepts the finished Select through statement=. It still selects
Customer entities, so DataR.stream yields typed Customers rather than raw rows.
The CTE, join, extra condition, ordering and limit all execute in SQL.
"""

import asyncio

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLField

from fastsprout.core import Field, ReadField
from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLEntity, SQLQuery, SQLSignpost

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
factory = async_sessionmaker(engine, expire_on_commit=False)
backend = SQLSignpost(factory)


class Customer(SQLEntity[int]):
    __signpost__ = backend

    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str]
    active: Field[bool] = Field(default=True)


class Order(SQLEntity[int]):
    __signpost__ = backend

    id: ReadField[int] = SQLField(primary_key=True)
    customer_id: Field[int]
    amount: Field[int]
    paid: Field[bool] = Field(default=True)


async def main() -> None:
    try:
        async with engine.begin() as connection:
            for entity in (Customer, Order):
                await connection.run_sync(entity.__table__.create)
        async with factory() as session:
            session.add_all(
                [
                    Customer(id=1, name="Ada"),
                    Customer(id=2, name="Grace"),
                    Customer(id=3, name="Linus", active=False),
                    Customer(id=4, name="Margaret"),
                    Order(id=1, customer_id=1, amount=80),
                    Order(id=2, customer_id=1, amount=70),
                    Order(id=3, customer_id=2, amount=200),
                    Order(id=4, customer_id=2, amount=100, paid=False),
                    Order(id=5, customer_id=3, amount=150),
                    Order(id=6, customer_id=3, amount=150),
                    Order(id=7, customer_id=4, amount=60),
                    Order(id=8, customer_id=4, amount=60),
                ]
            )
            await session.commit()

        paid_orders = (
            select(
                Order.customer_id.orm.label("customer_id"),
                func.sum(Order.amount.orm).label("total"),
            )
            .where(Order.paid.orm.is_(True))
            .group_by(Order.customer_id.orm)
            .having(func.count() >= 2, func.sum(Order.amount.orm) >= 100)
            .cte("paid_orders")
        )
        statement = (
            select(Customer)
            .join(paid_orders, Customer.id.orm == paid_orders.c.customer_id)
            .order_by(paid_orders.c.total.desc(), Customer.id.orm)
        )
        query = (
            SQLQuery(Customer, statement=statement)
            .where(Customer.active.eq(True))
            .limit(1)
        )

        print("Top active customer by paid order total:")
        async with DataR() as datar:
            async for customer in datar.stream(query):
                print(f"{customer.id}: {customer.name}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
