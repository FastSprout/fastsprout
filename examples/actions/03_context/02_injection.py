"""Pass an invocation value to a nested action without an argument.
The child declares Context() and receives the same RequestID as its parent."""

import asyncio
from typing import assert_type

from fastsprout.actions import action
from fastsprout.core import Context, Schema


class RequestID(str, Schema): ...


def get_request_id() -> RequestID:
    return RequestID("request-123")


@action
async def child(
    request_id: RequestID = Context(),
) -> RequestID:
    return request_id


@action
async def parent(
    request_id: RequestID = Context(get_request_id),
) -> tuple[RequestID, RequestID]:
    child_request_id = await child()

    return request_id, child_request_id


async def main() -> None:
    parent_request_id, child_request_id = await parent()
    assert_type(parent_request_id, RequestID)
    assert_type(child_request_id, RequestID)

    print(parent_request_id, child_request_id)


if __name__ == "__main__":
    asyncio.run(main())
