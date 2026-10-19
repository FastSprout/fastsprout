# 1. Function Steps

<!-- example-source: examples/testing/01_core/01_function_steps.py -->

Let pytest resolve typed function steps through fixture dependencies.

## Source

```python
"""Let pytest resolve typed function steps through fixture dependencies."""

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
@pytest.mark.parametrize("product_name", ["book", "pen"])
@pytest.mark.parametrize("count", [1])
def test_cart_count(added: CartContext, count: int) -> None:
    assert len(added.products) == count
```

## Result

```text

examples/testing/01_core/01_function_steps.py::test_cart_count[1-book] PASSED [ 50%]
examples/testing/01_core/01_function_steps.py::test_cart_count[1-pen] PASSED [100%]
```
