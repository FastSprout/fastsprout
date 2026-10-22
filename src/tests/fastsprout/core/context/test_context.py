import asyncio
from collections.abc import Callable
from typing import Literal

import pytest

from fastsprout.core import Context, Schema, dataclass, inject_depends
from fastsprout.core.context import ContextClass, current_context
from fastsprout.core.depends.scope import invocation_scope
from fastsprout.testing.core import given, then, when


@dataclass
class Request(Schema):
    name: str


class Other(Schema): ...


class TestContext:
    @given("a recorder of context provider calls")
    def calls(self) -> list[str]:
        return []

    @given("a context provider returning the request schema")
    def provider(self, calls: list[str]) -> Callable[[], Request]:
        def provide() -> Request:
            calls.append("provide")
            return Request("request")

        return provide

    @when(
        "a context value is resolved twice and then requested without a provider"
    )
    async def resolved(
        self,
        asynchronous: bool,
        calls: list[str],
        provider: Callable[[], Request],
    ) -> tuple[Request, Request, Request, list[str]]:
        def resolve(provider: Callable[..., Schema]) -> Schema:
            return provider()

        async def aresolve(provider: Callable[..., Schema]) -> Schema:
            return provider()

        marker = ContextClass(provider)
        with invocation_scope():
            if asynchronous:
                first = await marker.aresolve(Request, aresolve)
                second = await marker.aresolve(Request, aresolve)
                cached = await ContextClass().aresolve(Request, aresolve)
            else:
                default: Request = Context(provider)

                @inject_depends
                def read(value: Request = default) -> Request:
                    return value

                first = read()
                second = marker.resolve(Request, resolve)
                cached = ContextClass().resolve(Request, resolve)
        return first, second, cached, calls

    @pytest.mark.parametrize("asynchronous", [False, True])
    @then(
        "context providers run once per invocation and preserve object identity"
    )
    def test_cached(
        self, resolved: tuple[Request, Request, Request, list[str]]
    ) -> None:
        first, second, cached, calls = resolved
        assert first is second is cached
        assert first.name == "request"
        assert calls == ["provide"]

    @when("two concurrent callers request the same context value")
    async def concurrent(
        self, provider: Callable[[], Request]
    ) -> tuple[Request, Request]:
        async def resolve(callback: Callable[..., Schema]) -> Schema:
            await asyncio.sleep(0)
            return callback()

        marker = ContextClass(provider)
        with invocation_scope():
            first, second = await asyncio.gather(
                marker.aresolve(Request, resolve),
                marker.aresolve(Request, resolve),
            )
            return first, second

    @then("concurrent resolution shares one provider execution and one value")
    def test_concurrent(
        self, concurrent: tuple[Request, Request], calls: list[str]
    ) -> None:
        assert concurrent[0] is concurrent[1]
        assert calls == ["provide"]

    @when("a context is requested without a provider or with the wrong type")
    async def rejected(
        self,
        problem: Literal["missing", "wrong"],
        asynchronous: bool,
    ) -> RuntimeError | LookupError | TypeError | None:
        def resolve(provider: Callable[..., Schema]) -> Schema:
            return provider()

        async def aresolve(provider: Callable[..., Schema]) -> Schema:
            return provider()

        marker = ContextClass(Other if problem == "wrong" else None)

        try:
            with invocation_scope():
                if asynchronous:
                    await marker.aresolve(Request, aresolve)
                else:
                    marker.resolve(Request, resolve)
        except (RuntimeError, LookupError, TypeError) as error:
            return error
        return None

    @pytest.mark.parametrize("asynchronous", [False, True])
    @pytest.mark.parametrize(
        "problem, expected",
        [
            ("missing", LookupError),
            ("wrong", TypeError),
        ],
    )
    @then("invalid context requests raise a clear error")
    def test_rejected(
        self,
        rejected: RuntimeError | LookupError | TypeError | None,
        expected: type[RuntimeError] | type[LookupError] | type[TypeError],
    ) -> None:
        assert isinstance(rejected, expected)

    @when("context is accessed without an invocation")
    def outside_scope(self) -> RuntimeError | None:
        try:
            current_context()
        except RuntimeError as error:
            return error
        return None

    @then("context requires an active invocation")
    def test_outside_scope(self, outside_scope: RuntimeError | None) -> None:
        assert isinstance(outside_scope, RuntimeError)
        assert "action invocation" in str(outside_scope)

    @when("a context provider recursively requests its own type")
    async def circular(self) -> RuntimeError | None:
        marker = ContextClass(Request)

        async def resolve(provider: Callable[..., Schema]) -> Schema:
            return await marker.aresolve(Request, resolve)

        try:
            with invocation_scope():
                await marker.aresolve(Request, resolve)
        except RuntimeError as error:
            return error
        return None

    @then("circular context resolution fails before acquiring the same lock")
    def test_circular(self, circular: RuntimeError | None) -> None:
        assert isinstance(circular, RuntimeError)
        assert "Circular context" in str(circular)
