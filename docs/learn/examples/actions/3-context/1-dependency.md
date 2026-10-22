# 1. Dependency

<!-- example-source: examples/actions/03_context/01_dependency.py -->

Create an invocation value from a Context provider.
The provider runs when the action first needs RequestID.

## Source

```python
"""Create an invocation value from a Context provider.
The provider runs when the action first needs RequestID."""

import asyncio
from typing import assert_type

from fastsprout.actions import action
from fastsprout.core import Context, Schema


class RequestID(str, Schema): ...


def get_request_id() -> RequestID:
    return RequestID("request-123")


@action
async def handle(
    request_id: RequestID = Context(get_request_id),
) -> RequestID:
    return request_id


async def main() -> None:
    request_id = await handle()
    assert_type(request_id, RequestID)

    print(request_id)


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
request-123
```
