"""Parse step texts into typed pytest parameters.

Use `{name}` for strings, `{name:d}` for integers, and `{name:f}` for floats.
Fixture dependencies determine execution order.
"""

import pytest

from fastsprout.core import Field, dataclass
from fastsprout.testing.core import given, then, when


@dataclass
class CartContext:
    products: Field[list[str]] = Field(default_factory=list)


@given("the user has an empty cart")
def context() -> CartContext:
    return CartContext()


@when('the user adds "{product_name}"')
async def added(context: CartContext, product_name: str) -> CartContext:
    context.products.append(product_name)
    return context


@then("the cart contains {count:d} products")
@pytest.mark.steps(
    ('the user adds "book"', "the cart contains 1 products"),
    ('the user adds "pen"', "the cart contains 1 products"),
    ids=("book", "pen"),
)
def test_cart_count(added: CartContext, count: int) -> None:
    assert len(added.products) == count
