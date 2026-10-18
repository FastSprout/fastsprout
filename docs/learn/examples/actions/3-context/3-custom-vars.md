# 3. Custom Vars

<!-- example-source: examples/actions/03_context/03_custom_vars.py -->

Carry two independent typed values in one invocation.
RequestID and TenantID retain their own providers and can be serialized for worker handoff.

## Source

```python
"""Carry two independent typed values in one invocation.
RequestID and TenantID retain their own providers and can be serialized for worker handoff."""

import asyncio
from typing import assert_type
from uuid import UUID

from fastsprout.actions import action
from fastsprout.core import Context


class RequestID(str): ...


class TenantID(UUID): ...


def get_request_id() -> RequestID:
    return RequestID("request-123")


def get_tenant_id() -> TenantID:
    return TenantID("12345678-1234-5678-1234-567812345678")


@action
async def handle(
    request_id: RequestID = Context(get_request_id),
    tenant_id: TenantID = Context(get_tenant_id),
) -> tuple[RequestID, TenantID]:
    return request_id, tenant_id


async def main() -> None:
    request_id, tenant_id = await handle()
    assert_type(request_id, RequestID)
    assert_type(tenant_id, TenantID)

    print(request_id, tenant_id)


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
request-123 12345678-1234-5678-1234-567812345678
```
