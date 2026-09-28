from fastsprout.core import FastSproutError

__all__ = [
    "DataRError",
    "MissingCapabilityError",
    "NoActiveFlowError",
    "NoBackendError",
]


class DataRError(FastSproutError):
    """Base error of the data router."""


class NoBackendError(DataRError):
    """Entity class carries no `__signpost__` signpost."""


class NoActiveFlowError(DataRError):
    """Operation attempted outside an active DataR context."""


class MissingCapabilityError(DataRError):
    """The bound backend lacks the required data capability."""
