import asyncio
from weakref import ReferenceType, ref

import pytest

from fastsprout.core import Depends, inject_depends
from fastsprout.core.depends.invocation import with_dependencies
from fastsprout.core.depends.scope import current_dependency_cache


class TestInvocationDependencies:
    calls: list[str]
    values: list[ReferenceType[memoryview]]
    failure: type[BaseException] | None

    def source(self) -> int:
        self.calls.append("source")
        return 7

    def transient(self) -> memoryview:
        value = memoryview(b"dependency result")
        self.values.append(ref(value))
        return value

    async def execute(self, operation: str) -> None:
        self.calls.append(operation)
        if operation == "abort" and self.failure is not None:
            raise self.failure

    @pytest.mark.parametrize("use_cache", [True, False])
    @pytest.mark.parametrize(
        "failure", [None, ValueError, asyncio.CancelledError]
    )
    @inject_depends
    async def test_nested_providers_without_operation_arguments_share_cache(
        self, use_cache: bool, failure: type[BaseException] | None
    ) -> None:
        # given
        self.calls = []
        self.values = []
        self.failure = failure

        def nested(value: int = Depends(self.source)) -> int:
            self.calls.append("nested")
            return value

        def check(operation: str, value: int = Depends(nested)) -> None:
            assert value == 7

        guarded = with_dependencies(
            self.execute,
            [Depends(check), Depends(self.transient, use_cache=use_cache)],
        )

        # when
        await guarded("create")
        await guarded("delete")

        # then
        assert self.calls == ["source", "nested", "create", "delete"]
        cache = current_dependency_cache()
        assert cache is not None
        shared_size = len(cache)

        # when
        for _ in range(20):
            await guarded("update")
        if failure is not None:
            # when / then
            with pytest.raises(failure):
                await guarded("abort")

        # then
        assert all(value() is None for value in self.values)
        assert len(cache) == shared_size
        assert self.calls.count("source") == self.calls.count("nested") == 1
