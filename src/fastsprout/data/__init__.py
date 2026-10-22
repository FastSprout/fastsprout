from . import consts, entity, events, exceptions, types, utils
from .router import DataR, provide_datar
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
    "provide_datar",
    "types",
    "utils",
]

try:
    import fastsprout.data.backend.sql as sql

    from .relationship import Relationship as Relationship
except ModuleNotFoundError as error:
    error: ModuleNotFoundError
    if error.name not in {"sqlalchemy", "sqlmodel"}:
        raise
else:
    __all__ += ["Relationship", "sql"]
