__all__ = ["BaseFastSproutError", "FastSproutError"]


class BaseFastSproutError(Exception):
    """Base for all fastsprout exceptions."""


class FastSproutError(BaseFastSproutError):
    """Fastsprout exceptions."""
