from contextlib import nullcontext
from typing import Annotated

import pytest

from fastsprout.core import Depends, inject_depends
from fastsprout.core.depends.invocation import with_dependencies
from fastsprout.data import DataR, provide_datar
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.router.exceptions import DataRError

from .conftest import JoinCustomer


@pytest.mark.usefixtures("databases")
@pytest.mark.parametrize("reject", [False, True])
async def test_provider_shares_transaction_and_closes_after_action(
    monkeypatch: pytest.MonkeyPatch, reject: bool
) -> None:
    monkeypatch.setitem(
        inject_depends.dependency_providers, DataR, provide_datar
    )
    routers: list[DataR] = []

    async def create(data: Annotated[DataR, Depends()]) -> None:
        routers.append(data)
        await data.ability(JoinCustomer).create(
            JoinCustomer(id=12, name="Grace")
        )

    async def read(data: Annotated[DataR, Depends()]) -> None:
        assert data is routers[0]
        assert await data.stream(SQLQuery(entity=JoinCustomer)).count() == 3

    async def execute() -> None:
        if reject:
            raise ValueError("Rejected action")

    guarded = with_dependencies(execute, [Depends(create), Depends(read)])
    with (
        pytest.raises(ValueError, match="Rejected action")
        if reject
        else nullcontext()
    ):
        await guarded()

    async with DataR() as data:
        count = await data.stream(SQLQuery(entity=JoinCustomer)).count()
        assert count == (2 if reject else 3)
    with pytest.raises(DataRError, match="not initialized"):
        routers[0].ability(JoinCustomer)
