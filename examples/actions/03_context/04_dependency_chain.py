"""Build a Context value from a provider that uses Depends().
The computed TenantID is reused by nested actions without explicitly passing it along."""

import asyncio
from typing import assert_type

from fastsprout.actions import action
from fastsprout.core import Context, Depends, Schema, dataclass


class TenantID(str, Schema): ...


@dataclass(frozen=True)
class User:
    tenant_id: TenantID


def get_user() -> User:
    return User(
        tenant_id=TenantID("acme"),
    )


def get_tenant_id(
    user: User = Depends(get_user),
) -> TenantID:
    return user.tenant_id


@action
async def leaf(
    tenant_id: TenantID = Context(),
) -> TenantID:
    return tenant_id


@action
async def middle() -> TenantID:
    return await leaf()


@action
async def root(
    tenant_id: TenantID = Context(get_tenant_id),
) -> tuple[TenantID, TenantID]:
    nested_tenant_id = await middle()

    return tenant_id, nested_tenant_id


async def main() -> None:
    root_tenant_id, nested_tenant_id = await root()
    assert_type(root_tenant_id, TenantID)
    assert_type(nested_tenant_id, TenantID)

    print(root_tenant_id, nested_tenant_id)


if __name__ == "__main__":
    asyncio.run(main())
