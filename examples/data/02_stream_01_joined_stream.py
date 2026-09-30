"""Join three entity streams without a router or database."""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import assert_type

from fastsprout.data import JoinedStream


@dataclass(frozen=True)
class Order:
    id: int
    customer_id: int
    product_id: int


@dataclass(frozen=True)
class Customer:
    id: int
    name: str


@dataclass(frozen=True)
class Product:
    id: int
    name: str


async def stream[T](*items: T) -> AsyncIterator[T]:
    for item in items:
        yield item


async def main() -> None:
    orders = stream(
        Order(id=1, customer_id=10, product_id=20),
        Order(id=2, customer_id=10, product_id=21),
        Order(id=3, customer_id=99, product_id=20),
    )
    customers = stream(Customer(id=10, name="Ada"))
    products = stream(
        Product(id=20, name="Tea"),
        Product(id=21, name="Coffee"),
    )

    # Building the plan does not iterate any source.
    joined = (
        JoinedStream(orders)
        .join(customers, on=(lambda row: row[0].customer_id, lambda c: c.id))
        .join(products, on=(lambda row: row[0].product_id, lambda p: p.id))
    )
    rows = await joined.to_list()
    assert_type(rows, list[tuple[Order, Customer, Product]])
    result = [
        (order.id, customer.name, product.name)
        for order, customer, product in rows
    ]
    assert result == [(1, "Ada", "Tea"), (2, "Ada", "Coffee")]
    print(result)

    # The third order has no matching customer, so the inner join omits it.
    # Uncomment to see mypy/basedpyright reject a field on the wrong entity:
    # joined.join(products, on=(lambda row: row[1].product_id, lambda p: p.id))


if __name__ == "__main__":
    asyncio.run(main())
