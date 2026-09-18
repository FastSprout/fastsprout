import asyncio
from contextlib import aclosing

import pytest

from fastsprout.data import DataR, JoinedStream, SimpleAsyncValueStream
from fastsprout.data.backend.sql import SQLQuery
from fastsprout.data.exceptions import MixedStreamContextsError, NoSessionError

from .conftest import JoinCustomer, JoinOrder


@pytest.mark.usefixtures("databases")
class TestJoinedStreamContext:
    @pytest.mark.parametrize("shared", [False, True])
    @pytest.mark.parametrize(
        "transform",
        [
            pytest.param(lambda stream: stream, id="direct"),
            pytest.param(lambda stream: stream.take(2), id="sql-limit"),
            pytest.param(
                lambda stream: stream.filter(lambda _: True), id="python-filter"
            ),
        ],
    )
    async def test_entity_streams_require_one_context(self, shared, transform):
        # given
        async with DataR() as first, DataR() as second:
            right_router = first if shared else second
            stream = JoinedStream(
                transform(first.stream(SQLQuery(entity=JoinOrder)))
            ).join(
                transform(right_router.stream(SQLQuery(entity=JoinCustomer))),
                on=(
                    lambda row: row[0].customer_id,
                    lambda customer: customer.id,
                ),
            )
            # when / then
            if shared:
                rows = await stream.to_list()
                assert [
                    (order.id, customer.id) for order, customer in rows
                ] == [(1, 10), (2, 11)]
            else:
                with pytest.raises(
                    MixedStreamContextsError, match="same DataR context"
                ):
                    await stream.to_list()

    async def test_same_entity_from_different_contexts_is_rejected(self):
        # given
        async with DataR() as first, DataR() as second:
            stream = JoinedStream(
                first.stream(SQLQuery(entity=JoinCustomer))
            ).join(
                second.stream(SQLQuery(entity=JoinCustomer)),
                on=(lambda row: row[0].id, lambda customer: customer.id),
            )
            # when / then
            with pytest.raises(
                MixedStreamContextsError, match="same DataR context"
            ):
                await stream.to_list()

    async def test_contexts_own_sessions_without_changing_the_entity_signpost(
        self,
    ):
        # given
        signpost = JoinCustomer.__signpost__
        factory = signpost.factory
        async with DataR() as first, DataR() as second:
            # when
            first_rows = await first.stream(
                SQLQuery(entity=JoinCustomer)
            ).to_list()
            repeated = await first.stream(
                SQLQuery(entity=JoinCustomer)
            ).to_list()
            second_rows = await second.stream(
                SQLQuery(entity=JoinCustomer)
            ).to_list()
            # then
            assert first_rows[0] is repeated[0]
            assert first_rows[0] is not second_rows[0]
            assert JoinCustomer.__signpost__ is signpost
            assert signpost.factory == factory

    @pytest.mark.parametrize("empty_side", ["left", "right"])
    async def test_empty_sources_do_not_hide_mixed_contexts(self, empty_side):
        # given
        async with DataR() as first, DataR() as second:
            left = first.stream(SQLQuery(entity=JoinOrder))
            right = second.stream(SQLQuery(entity=JoinCustomer))
            stream = JoinedStream(
                left.take(0) if empty_side == "left" else left
            ).join(
                right.take(0) if empty_side == "right" else right,
                on=(lambda _: 0, lambda _: 0),
            )
            # when / then
            with pytest.raises(
                MixedStreamContextsError, match="same DataR context"
            ):
                await stream.to_list()

    async def test_column_projections_preserve_context(self):
        # given
        async with DataR() as first, DataR() as second:
            stream = JoinedStream(
                first.stream(SQLQuery(entity=JoinOrder)).to_values(
                    JoinOrder.customer_id
                )
            ).join(
                second.stream(SQLQuery(entity=JoinCustomer)).to_values(
                    JoinCustomer.id
                ),
                on=(lambda row: row[0], lambda identifier: identifier),
            )
            # when / then
            with pytest.raises(
                MixedStreamContextsError, match="same DataR context"
            ):
                await stream.to_list()

    @pytest.mark.parametrize("values", [False, True])
    async def test_started_iterators_preserve_context(self, values):
        # given
        async with DataR() as first, DataR() as second:
            left = first.stream(SQLQuery(entity=JoinOrder))
            right = second.stream(SQLQuery(entity=JoinCustomer))
            async with (
                aclosing(
                    aiter(
                        left.to_values(JoinOrder.customer_id)
                        if values
                        else left
                    )
                ) as left_iterator,
                aclosing(
                    aiter(right.to_values(JoinCustomer.id) if values else right)
                ) as right_iterator,
            ):
                await anext(left_iterator)
                await anext(right_iterator)
                stream = JoinedStream(left_iterator).join(
                    right_iterator, on=(lambda _: 0, lambda _: 0)
                )
                # when / then
                with pytest.raises(
                    MixedStreamContextsError, match="same DataR context"
                ):
                    await stream.to_list()

    async def test_chained_join_keeps_context_through_memory_source(self):
        # given
        async with DataR() as first, DataR() as second:
            stream = (
                JoinedStream(first.stream(SQLQuery(entity=JoinOrder)))
                .join(
                    SimpleAsyncValueStream([10, 11]),
                    on=(lambda row: row[0].customer_id, lambda item: item),
                )
                .join(
                    second.stream(SQLQuery(entity=JoinCustomer)),
                    on=(lambda row: row[1], lambda customer: customer.id),
                )
            )
            # when / then
            with pytest.raises(
                MixedStreamContextsError, match="same DataR context"
            ):
                await stream.to_list()

    async def test_separate_joins_can_run_concurrently(self):
        # given
        async with DataR() as first, DataR() as second:
            left = JoinedStream(first.stream(SQLQuery(entity=JoinOrder)))
            right = JoinedStream(second.stream(SQLQuery(entity=JoinCustomer)))
            # when
            orders, customers = await asyncio.gather(
                left.to_list(), right.to_list()
            )
            # then
            assert len(orders) == 3
            assert len(customers) == 2

    async def test_iteration_does_not_leak_context_to_its_consumer(self):
        # given
        async with DataR() as first, DataR() as second:
            left = JoinedStream(first.stream(SQLQuery(entity=JoinOrder)))
            right = JoinedStream(second.stream(SQLQuery(entity=JoinCustomer)))
            # when / then
            async with aclosing(aiter(left)) as iterator:
                await anext(iterator)
                assert len(await right.to_list()) == 2
                await anext(iterator)

    @pytest.mark.parametrize("reenter", [False, True])
    async def test_stream_cannot_outlive_its_original_context(self, reenter):
        # given
        data = DataR()
        async with data:
            stream = JoinedStream(data.stream(SQLQuery(entity=JoinOrder)))
        # when / then
        if reenter:
            async with data:
                with pytest.raises(NoSessionError, match="no longer active"):
                    await stream.to_list()
        else:
            with pytest.raises(NoSessionError, match="no longer active"):
                await stream.to_list()

    async def test_started_join_cannot_resume_after_its_context_closes(self):
        # given
        async with DataR() as data:
            iterator = aiter(data.join(SQLQuery(entity=JoinOrder)))
            await anext(iterator)
        # when / then
        async with aclosing(iterator):
            with pytest.raises(NoSessionError, match="no longer active"):
                await anext(iterator)
