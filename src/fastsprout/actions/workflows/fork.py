from fastsprout.core import Schema, dataclass

__all__ = ["ForkResult"]


@dataclass(frozen=True)
class ForkResult[A: Schema, B: Schema](Schema):
    left: A
    right: B
