import asyncio
from collections.abc import AsyncIterator, Callable
from contextlib import nullcontext
from typing import assert_type

import pytest

from fastsprout.actions import ForkResult, Workflow, action
from fastsprout.core import Context, Depends

from ..types.common import Amount, Computed


class TestWorkflowFork:
    @pytest.fixture
    def calls(self) -> list[str]:
        return []

    @pytest.fixture
    def resource(self, calls: list[str]) -> Callable[[], AsyncIterator[None]]:
        async def provide() -> AsyncIterator[None]:
            calls.append("open")
            outcome = "rollback"
            try:
                yield None
                outcome = "commit"
            finally:
                calls.append(outcome)

        return provide

    async def test_fork_runs_concurrently_and_shares_invocation_context(
        self,
    ) -> None:
        # given
        left_started = asyncio.Event()
        right_started = asyncio.Event()
        request_ids = iter(("request-1", "request-2"))

        @action
        async def first(
            value: Amount, request_id: str = Context(lambda: next(request_ids))
        ) -> Amount:
            assert request_id == "request-1"
            return value

        @action
        async def left(value: Amount, request_id: str = Context()) -> Computed:
            left_started.set()
            await right_started.wait()
            return Computed(value=value.value * 2, request_id=request_id)

        @action
        async def right(value: Amount, request_id: str = Context()) -> Computed:
            right_started.set()
            await left_started.wait()
            return Computed(value=value.value * 4, request_id=request_id)

        @action
        async def join(results: ForkResult[Computed, Computed]) -> Amount:
            assert (
                results.left.request_id
                == results.right.request_id
                == "request-1"
            )
            return Amount(value=results.left.value + results.right.value)

        workflow = Workflow(first).fork(left, right).join(join)

        # when
        async with asyncio.timeout(1):
            results = [item async for item in workflow(Amount(value=3))]

        # then
        assert len(results) == 1
        result = results[0]
        assert_type(result, Amount)
        assert result.value == 18
        assert next(request_ids) == "request-2"
        assert Amount.model_validate_json(result.model_dump_json()) == result

    @pytest.mark.parametrize("fail", [False, True], ids=["success", "failure"])
    async def test_fork_result_keeps_concrete_schema_fields(
        self,
        fail: bool,
        calls: list[str],
        resource: Callable[[], AsyncIterator[None]],
    ) -> None:
        # given
        @action(dependencies=[Depends(resource)])
        async def first(value: Amount) -> Amount:
            return value

        async def compute(value: Amount) -> Computed:
            assert calls == ["open"]
            if fail:
                raise ValueError("Fork failed")
            return Computed(value=value.value, request_id="request-1")

        workflow = Workflow(first).fork(first, compute)

        # then
        with (
            pytest.raises(ValueError, match="Fork failed")
            if fail
            else nullcontext()
        ):
            results = [item async for item in workflow(Amount(value=3))]
            result = results[0]
            assert_type(result, ForkResult[Amount, Computed])
            assert result.left.value == 3
            assert result.right.value == 3
            assert result.right.request_id == "request-1"

        # then
        assert calls == ["open", "rollback" if fail else "commit"]
