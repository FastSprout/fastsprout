from . import consts, entity, events, exceptions, types, utils
from .router import DataR
from .streams.implementation import (
    JoinedStream,
    SimpleAsyncEntityStream,
    SimpleAsyncValueStream,
)

__all__ = [
    "DataR",
    "JoinedStream",
    "SimpleAsyncEntityStream",
    "SimpleAsyncValueStream",
    "consts",
    "entity",
    "events",
    "exceptions",
    "types",
    "utils",
]

try:
    from .backend import sql as sql
    from .relationship import Relationship as Relationship
except ModuleNotFoundError as error:
    if error.name not in {"sqlalchemy", "sqlmodel"}:
        raise
else:
    __all__.extend(["Relationship", "sql"])
