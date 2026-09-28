import asyncio
from typing import Final, Literal

__all__ = [
    "ALL_COMPLETED",
    "FIRST_COMPLETED",
    "FIRST_EXCEPTION",
]

FIRST_COMPLETED: Final[Literal["FIRST_COMPLETED"]] = asyncio.FIRST_COMPLETED
FIRST_EXCEPTION: Final[Literal["FIRST_EXCEPTION"]] = asyncio.FIRST_EXCEPTION
ALL_COMPLETED: Final[Literal["ALL_COMPLETED"]] = asyncio.ALL_COMPLETED
