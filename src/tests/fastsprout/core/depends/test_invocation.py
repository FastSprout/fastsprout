import asyncio
from weakref import ReferenceType, ref

import pytest

from fastsprout.core import Chunk, Depends, inject_depends
from fastsprout.core.depends import DependsClass
from fastsprout.core.depends.invocation import with_dependencies
from fastsprout.core.depends.scope import current_dependency_cache
from fastsprout.core.types.iterable import resolve_any_iterable
from fastsprout.testing.core import given, then, when


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
            # then
            with pytest.raises(failure):
                await guarded("abort")

        # then
        assert all(value() is None for value in self.values)
        assert len(cache) == shared_size
        assert self.calls.count("source") == self.calls.count("nested") == 1


class TestChunkReplacement:
    @given("a dependency returning a replacement chunk")
    def replacement(self) -> DependsClass:
        def replace() -> Chunk[int]:
            return Chunk(resolve_any_iterable([7]))

        return Depends(replace)

    @when("an operation without exactly one chunk receives a replacement")
    async def rejected(
        self, replacement: DependsClass, two_chunks: bool
    ) -> TypeError | None:
        async def execute(
            left: Chunk[int] | None, right: Chunk[int] | None
        ) -> None:
            raise AssertionError("Invalid chunk replacement ran the operation")

        guarded = with_dependencies(execute, [replacement])
        try:
            await guarded(
                Chunk(resolve_any_iterable([1])) if two_chunks else None,
                Chunk(resolve_any_iterable([2])) if two_chunks else None,
            )
        except TypeError as error:
            return error
        return None

    @pytest.mark.parametrize("two_chunks", [False, True])
    @then("ambiguous or missing chunk arguments reject the dependency result")
    def test_replacement_target(self, rejected: TypeError | None) -> None:
        assert isinstance(rejected, TypeError)
        assert str(rejected) == (
            "A Chunk result requires exactly one Chunk argument"
        )
