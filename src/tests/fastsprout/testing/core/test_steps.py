from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest

from fastsprout.testing.core import given, then, when, when_then
from tests.type_checking import TypeChecker

from .common import CartContext

type ResourceSteps = Iterator[list[str]]
type AsyncResourceSteps = AsyncIterator[list[str]]


class BaseCartCases:
    def make_context(self) -> CartContext:
        return CartContext()

    @given("the user has an empty cart")
    def cart(self) -> CartContext:
        return self.make_context()

    @when('the user adds "{product_name}"')
    async def added(self, cart: CartContext, product_name: str) -> CartContext:
        cart.products.append(product_name)
        return cart

    @then("the cart contains {count:d} products")
    @pytest.mark.steps(
        (
            "the user has an empty cart",
            'the user adds "book"',
            "the cart contains 1 products",
        ),
        (
            "the user has an empty cart",
            'the user adds "pen"',
            "the cart contains 1 products",
        ),
    )
    def test_cart_count(
        self, cart: CartContext, added: CartContext, count: int
    ) -> None:
        assert added is cart
        assert len(cart.products) == count


class TestClassSteps(BaseCartCases):
    pass


class TestInheritedSteps(BaseCartCases):
    def make_context(self) -> CartContext:
        return CartContext(products=[])


@given("the user has an empty cart")
def cart() -> CartContext:
    return CartContext()


@when('the user adds "{product_name}"')
async def added(cart: CartContext, product_name: str) -> CartContext:
    cart.products.append(product_name)
    return cart


class TestFunctionSteps:
    @then("the cart contains {count:d} products")
    @pytest.mark.parametrize("product_name", ["book", "pen"])
    @pytest.mark.parametrize("count", [1])
    def test_cart_count(
        self, cart: CartContext, added: CartContext, count: int
    ) -> None:
        assert added is cart
        assert len(cart.products) == count

    @when_then("the empty cart can be updated")
    async def test_combined_phase(
        self, cart: CartContext, count: int = 1
    ) -> None:
        cart.products.append("book")
        assert len(cart.products) == count


class TestFixtureLifetimes:
    @given("an iterator returned as the fixture value")
    def values(self) -> Iterator[int]:
        return iter((1, 2))

    @given("a synchronous resource")
    def resource(self) -> ResourceSteps:
        steps = ["given"]
        yield steps
        assert steps == ["given", "then"]

    @given("an asynchronous resource")
    async def async_resource(self) -> AsyncResourceSteps:
        steps = ["given"]
        yield steps
        assert steps == ["given", "then"]

    @then("both resources are available")
    async def test_resources(
        self,
        resource: list[str],
        async_resource: list[str],
        values: Iterator[int],
    ) -> None:
        assert resource == async_resource == ["given"]
        resource.append("then")
        async_resource.append("then")
        assert list(values) == [1, 2]


class TestTyping:
    def test_typing(self, type_checker: TypeChecker) -> None:
        # given
        source = Path(__file__).with_name("steps_typing.py.txt")
        # when / then
        type_checker.check(source)
