import pytest
from sqlalchemy import event, select

from fastsprout.data import DataR, JoinedStream, SimpleAsyncValueStream
from fastsprout.data.backend.sql import SQLQuery
from fastsprout.data.router.exceptions import DataRError

from .conftest import JoinCustomer, JoinOrder, JoinProduct


async def test_building_a_routed_join_executes_no_queries(databases) -> None:
    statements = []

    def record(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    for engine in databases:
        event.listen(engine.sync_engine, "before_cursor_execute", record)
    async with DataR() as data:
        stream = data.join(SQLQuery(entity=JoinOrder)).join(
            SQLQuery(entity=JoinCustomer),
            on=(lambda row: row[0].customer_id, lambda customer: customer.id),
        )
        assert statements == []
        assert len(await stream.to_list()) == 2
        assert len(statements) == 2


async def test_join_routes_three_sources_across_two_databases(
    databases,
) -> None:
    async with DataR() as data:
        stream = (
            data.join(SQLQuery(entity=JoinOrder))
            .join(
                SQLQuery(entity=JoinCustomer),
                on=(
                    lambda row: row[0].customer_id,
                    lambda customer: customer.id,
                ),
            )
            .join(
                SQLQuery(entity=JoinProduct),
                on=(lambda row: row[0].product_id, lambda product: product.id),
            )
        )
        rows = [row async for row in stream]
        assert [
            (order.id, customer.name, product.name)
            for order, customer, product in rows
        ] == [
            (1, "Ada", "Tea"),
            (2, "Lin", "Coffee"),
        ]


async def test_join_respects_query_statements_limits_and_offsets(
    databases,
) -> None:
    async with DataR() as data:
        stream = data.join(SQLQuery(entity=JoinOrder).offset(1).limit(1)).join(
            SQLQuery(
                entity=JoinCustomer,
                statement=select(JoinCustomer).where(JoinCustomer.id.orm == 11),
            ),
            on=(lambda row: row[0].customer_id, lambda customer: customer.id),
        )
        assert [
            (order.id, customer.name)
            for order, customer in await stream.to_list()
        ] == [(2, "Lin")]


async def test_routed_branches_are_independent_and_see_pending_writes(
    databases,
) -> None:
    async with DataR() as data:
        await data.ability(JoinCustomer).bulk_create(
            [JoinCustomer(id=99, name="New")]
        )
        base = data.join(SQLQuery(entity=JoinOrder))
        customers = base.join(
            SQLQuery(entity=JoinCustomer),
            on=(lambda row: row[0].customer_id, lambda customer: customer.id),
        )
        products = base.join(
            SQLQuery(entity=JoinProduct),
            on=(lambda row: row[0].product_id, lambda product: product.id),
        )
        assert [customer.name for _, customer in await customers.to_list()] == [
            "Ada",
            "Lin",
            "New",
        ]
        assert [product.name for _, product in await products.to_list()] == [
            "Tea",
            "Coffee",
            "Tea",
        ]
        assert [order.id for (order,) in await base.to_list()] == [1, 2, 3]


async def test_standalone_join_combines_sql_and_memory_streams(
    databases,
) -> None:
    async with DataR() as data:
        stream = JoinedStream(data.stream(SQLQuery(entity=JoinOrder))).join(
            SimpleAsyncValueStream([10, 11]),
            on=(
                lambda row: row[0].customer_id,
                lambda customer_id: customer_id,
            ),
        )
        assert [
            (order.id, customer_id)
            for order, customer_id in await stream.to_list()
        ] == [(1, 10), (2, 11)]


async def test_join_requires_an_active_router_context(databases) -> None:
    with pytest.raises(DataRError, match="not initialized"):
        DataR().join(SQLQuery(entity=JoinOrder))


@pytest.mark.parametrize("chained", [False, True])
async def test_join_rejects_streams_from_another_router(databases, chained):
    # given
    async with DataR() as data, DataR() as other:
        foreign = other.stream(SQLQuery(entity=JoinCustomer))
        # when / then
        with pytest.raises(DataRError, match="Not supported source"):
            if chained:
                data.join(SQLQuery(entity=JoinOrder)).join(
                    foreign,
                    on=(
                        lambda row: row[0].customer_id,
                        lambda customer: customer.id,
                    ),
                )
            else:
                data.join(foreign)


async def test_all_join_sources_share_pending_writes_and_abort(databases):
    # given
    async with DataR() as data:
        await data.ability(JoinOrder).create(
            JoinOrder(id=4, customer_id=12, product_id=22)
        )
        await data.ability(JoinCustomer).create(JoinCustomer(id=12, name="New"))
        await data.ability(JoinProduct).create(JoinProduct(id=22, name="Cake"))
        stream = (
            data.join(SQLQuery(entity=JoinOrder))
            .join(
                SQLQuery(entity=JoinCustomer),
                on=(
                    lambda row: row[0].customer_id,
                    lambda customer: customer.id,
                ),
            )
            .join(
                SQLQuery(entity=JoinProduct),
                on=(lambda row: row[0].product_id, lambda product: product.id),
            )
        )
        # when
        rows = await stream.to_list()
        # then
        assert [
            (order.id, customer.id, product.id)
            for order, customer, product in rows
        ] == [(1, 10, 20), (2, 11, 21), (4, 12, 22)]
        # when
        await data.abort()
        rows = await stream.to_list()
        # then
        assert [
            (order.id, customer.id, product.id)
            for order, customer, product in rows
        ] == [(1, 10, 20), (2, 11, 21)]


@pytest.mark.parametrize("chained", [False, True])
async def test_join_requires_queries_instead_of_entity_classes(
    databases, chained
) -> None:
    async with DataR() as data:
        with pytest.raises(DataRError, match="Not supported source"):
            if chained:
                data.join(SQLQuery(entity=JoinOrder)).join(
                    JoinCustomer,
                    on=(
                        lambda row: row[0].customer_id,
                        lambda customer: customer.id,
                    ),
                )
            else:
                data.join(JoinOrder)
