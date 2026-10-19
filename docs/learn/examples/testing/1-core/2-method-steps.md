# 2. Method Steps

<!-- example-source: examples/testing/01_core/02_method_steps.py -->

Write pytest cases once and inherit them for different providers.

## Source

```python
"""Write pytest cases once and inherit them for different providers."""

import pytest

from fastsprout.core import Field, dataclass
from fastsprout.testing.core import given, then, when


@dataclass
class Cart:
    products: Field[list[str]] = Field(default_factory=list)

    def add(self, name: str) -> None:
        self.products.append(name)


class CheckedCart(Cart):
    def add(self, name: str) -> None:
        if not name:
            raise ValueError("A product needs a name")
        super().add(name)


class CartCases:
    cart_type: type[Cart] = Cart

    @given("the user has an empty cart")
    def cart(self) -> Cart:
        return self.cart_type()

    @when('the user adds "{product_name}"')
    async def added(self, cart: Cart, product_name: str) -> Cart:
        cart.add(product_name)
        return cart

    @then("the cart contains {count:d} products")
    @pytest.mark.parametrize("product_name", ["book", "pen"])
    @pytest.mark.parametrize("count", [1])
    def test_cart_count(self, added: Cart, count: int) -> None:
        assert len(added.products) == count


class TestCart(CartCases):
    pass


class TestCheckedCart(CartCases):
    cart_type = CheckedCart
```

## Result

```text

examples/testing/01_core/02_method_steps.py::TestCart::test_cart_count[1-book] PASSED [ 25%]
examples/testing/01_core/02_method_steps.py::TestCart::test_cart_count[1-pen] PASSED [ 50%]
examples/testing/01_core/02_method_steps.py::TestCheckedCart::test_cart_count[1-book] PASSED [ 75%]
examples/testing/01_core/02_method_steps.py::TestCheckedCart::test_cart_count[1-pen] PASSED [100%]
```
