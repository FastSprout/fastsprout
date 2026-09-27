from typing import Literal

__all__ = ["ReturnWhenLiteral"]


type ReturnWhenLiteral = Literal[
    "FIRST_COMPLETED", "FIRST_EXCEPTION", "ALL_COMPLETED"
]
