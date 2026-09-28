from typing import Any, Final

__all__ = ["Undefined", "UndefinedType"]


class UndefinedType:
    """Sentinel type for 'no value provided'.

    fastsprout's own `PydanticUndefined`: a single shared singleton,
    falsy, safe to copy/pickle, usable anywhere a missing value must be
    distinguished from `None` (which is a real value).
    """

    __slots__ = ()

    def __bool__(self) -> bool:
        return False

    def __copy__(self) -> "UndefinedType":
        return self

    def __deepcopy__(self, memo: dict[int, Any]) -> "UndefinedType":
        return self

    def __reduce__(self) -> str:
        return "Undefined"

    def __repr__(self) -> str:
        return "Undefined"


Undefined: Final[UndefinedType] = UndefinedType()
