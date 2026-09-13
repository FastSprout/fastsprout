from fastsprout.core.exceptions import FastSproutError

__all__ = [
    "FSDataError",
    "NoPrimaryKeyError",
    "NoSessionError",
    "NotFoundError",
    "OffsetExceededError",
]


class FSDataError(FastSproutError):
    """Base exception for all data errors."""


class NotFoundError(FSDataError):
    """Raised when a requested entity is not found."""


class NoSessionError(FSDataError):
    """Raised when no session is available."""


class NoPrimaryKeyError(FSDataError):
    """Raised when a entity has no primary key defined."""


class OffsetExceededError(FSDataError):
    """Raised when pagination offset exceeds total count."""
