__all__ = ["FieldAssignment"]


class FieldAssignment[T]:
    """Typed assignment used for partial entity updates.

    Two FieldAssignments are equal when both name AND value match.

    Usage:
        Hero.is_active.set(True)             # FieldAssignment[bool]
        repo.update(hero_id, [Hero.name.set("Spider")])
    """

    __slots__ = ("name", "value")

    def __init__(self, name: str, value: T) -> None:
        self.name = name
        self.value: T = value

    def __repr__(self) -> str:
        return f"FieldAssignment(name={self.name!r}, value={self.value!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FieldAssignment):
            return NotImplemented
        return self.name == other.name and self.value == other.value

    def __hash__(self) -> int:
        return hash((self.name, self.value))
