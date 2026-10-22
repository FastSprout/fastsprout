"""Workflow — typed state."""

import asyncio
from typing import assert_type

from fastsprout.actions import Workflow, action
from fastsprout.core import BaseSchema


class OrderState(BaseSchema):
    quantity: int
    unit_price: int
    total: int = 0
    paid: bool = False


@action
async def calculate(
    state: OrderState,
) -> OrderState:
    return state.model_copy(
        update={
            "total": state.quantity * state.unit_price,
        }
    )


@action
async def pay(
    state: OrderState,
) -> OrderState:
    return state.model_copy(
        update={
            "paid": True,
        }
    )


workflow = Workflow(calculate).then(pay)


async def main() -> None:
    async for state in workflow(
        OrderState(
            quantity=2,
            unit_price=50,
        )
    ):
        assert_type(state, OrderState)
        print(state)


if __name__ == "__main__":
    asyncio.run(main())
