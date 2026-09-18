from contextlib import AsyncExitStack

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLField

from fastsprout.core import Field
from fastsprout.data.backend.sql import SQLEntity
from fastsprout.data.backend.sql.entity import SQLSignpost


class JoinOrder(SQLEntity[int]):
    id: Field[int] = SQLField(primary_key=True)
    customer_id: Field[int]
    product_id: Field[int]


class JoinCustomer(SQLEntity[int]):
    id: Field[int] = SQLField(primary_key=True)
    name: Field[str]


class JoinProduct(SQLEntity[int]):
    id: Field[int] = SQLField(primary_key=True)
    name: Field[str]


@pytest.fixture
async def databases():
    engines = []
    async with AsyncExitStack() as stack:
        for entities, rows in [
            (
                [JoinOrder],
                [
                    JoinOrder(id=1, customer_id=10, product_id=20),
                    JoinOrder(id=2, customer_id=11, product_id=21),
                    JoinOrder(id=3, customer_id=99, product_id=20),
                ],
            ),
            (
                [JoinCustomer, JoinProduct],
                [
                    JoinCustomer(id=10, name="Ada"),
                    JoinCustomer(id=11, name="Lin"),
                    JoinProduct(id=20, name="Tea"),
                    JoinProduct(id=21, name="Coffee"),
                ],
            ),
        ]:
            engine = create_async_engine("sqlite+aiosqlite:///:memory:")
            engines.append(engine)
            stack.push_async_callback(engine.dispose)
            async with engine.begin() as connection:
                for entity in entities:
                    await connection.run_sync(entity.__table__.create)
            factory = async_sessionmaker(engine, expire_on_commit=False)
            signpost = SQLSignpost(factory)
            for entity in entities:
                entity.__signpost__ = signpost
            async with factory() as session:
                session.add_all(rows)
                await session.commit()
        yield engines
