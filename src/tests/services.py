from asyncio import get_running_loop, sleep, timeout
from collections.abc import Awaitable, Callable


async def wait_for_service(connect: Callable[[], Awaitable[None]]) -> None:
    deadline = get_running_loop().time() + 120
    while True:
        try:
            async with timeout(5):
                await connect()
        except Exception:
            if get_running_loop().time() >= deadline:
                raise
            await sleep(1)
        else:
            return
