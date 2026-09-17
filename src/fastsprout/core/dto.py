"""DTO derivation with visibility checked by ordinary Python type checkers."""

from collections.abc import Callable
from copy import deepcopy
from dataclasses import MISSING, dataclass, fields, is_dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Literal, Never

from .fields.field import Field
from .types.undefined import Undefined

__all__ = ["ReadDTO", "ReadWriteDTO", "WriteDTO", "dto"]


if TYPE_CHECKING:
    from fastsprout.core.fields.metaclass import TypedModelMeta
    from fastsprout.data.backend.sql.entity import TypedSQLMeta

    class _DTOMeta(TypedSQLMeta, TypedModelMeta):
        """Static view of the DTO branch in the entity metaclasses.

        DTOs bypass model construction, so do not reapply the entity
        metaclasses' dataclass transforms to their constructors.
        """

else:
    # Let Python select the source entity's metaclass at runtime. Its DTO
    # branch already skips Pydantic construction and SQLAlchemy mapping.
    _DTOMeta = type


@dataclass(frozen=True)
class _Definition:
    allowed: frozenset[str]
    required: frozenset[str]
    defaults: dict[str, Callable[[dict[str, Any]], Any]]


class _DTO(metaclass=_DTOMeta):
    __fastsprout_operations__: ClassVar[frozenset[str]]
    __fastsprout_forbidden__: ClassVar[frozenset[str]]
    __fastsprout_source__: ClassVar[type]
    __fastsprout_definition__: ClassVar[_Definition]

    def __init_subclass__(
        cls, *, init: Literal[False] = False, **kwargs: Any
    ) -> None:
        if init:
            raise TypeError("DTO classes require init=False")
        super().__init_subclass__(**kwargs)
        # The visibility bases themselves are declared before dto() below.
        # Concrete DTOs are created after module initialization, when their
        # source entity and its descriptors are already complete.
        if _DTO not in cls.__bases__:
            dto(cls)

    def __init__(self, **values: Any) -> None:
        definition = _definition(type(self))
        for name in values:
            _check_name(type(self), name, definition)
        missing = definition.required - values.keys()
        if missing:
            raise TypeError(f"Missing DTO fields: {', '.join(sorted(missing))}")
        data = values.copy()
        for name, factory in definition.defaults.items():
            if name not in data:
                data[name] = factory(data)
        object.__setattr__(self, "__dict__", data)

    if not TYPE_CHECKING:

        def __getattr__(self, name: str) -> Never:
            _check_name(type(self), name, _definition(type(self)))
            raise AttributeError(f"DTO field {name!r} has not been set")

    def __setattr__(self, name: str, value: Any) -> None:
        _check_name(type(self), name, _definition(type(self)))
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        _check_name(type(self), name, _definition(type(self)))
        try:
            del vars(self)[name]
        except KeyError:
            raise AttributeError(name) from None

    def __repr__(self) -> str:
        definition = _definition(type(self))
        body = ", ".join(
            f"{key}={value!r}"
            for key, value in self.__dict__.items()
            if key in definition.allowed
        )
        return f"{type(self).__name__}({body})"

    @classmethod
    def model_validate(cls, *args: Any, **kwargs: Any) -> Never:
        raise TypeError("DTOs use their constructor; validate at the boundary")

    @classmethod
    def model_validate_json(cls, *args: Any, **kwargs: Any) -> Never:
        raise TypeError("DTOs use their constructor; validate at the boundary")

    @classmethod
    def model_validate_strings(cls, *args: Any, **kwargs: Any) -> Never:
        raise TypeError("DTOs use their constructor; validate at the boundary")

    @classmethod
    def model_construct(cls, *args: Any, **kwargs: Any) -> Never:
        raise TypeError("DTOs use their constructor")


class ReadDTO(_DTO):
    """Use first in the bases of a read DTO, followed by the source entity."""

    __fastsprout_operations__: ClassVar[frozenset[str]] = frozenset({"read"})

    @property
    def _fastsprout_visibility(self) -> Literal["read"]:
        return "read"


class WriteDTO(_DTO):
    """Use first in the bases of a write DTO, followed by the source entity."""

    __fastsprout_operations__: ClassVar[frozenset[str]] = frozenset({"write"})

    @property
    def _fastsprout_visibility(self) -> Literal["write"]:
        return "write"


class ReadWriteDTO(_DTO):
    """Union of read and write fields; internal fields are still forbidden."""

    __fastsprout_operations__: ClassVar[frozenset[str]] = frozenset(
        {"read", "write"}
    )

    @property
    def _fastsprout_visibility(self) -> Literal["read_write"]:
        return "read_write"


def is_dto_base(base: type) -> bool:
    """Model metaclasses must not validate or map DTO subclasses."""
    return issubclass(base, _DTO)


def _definition(cls: type[_DTO]) -> _Definition:
    definition = vars(cls).get("__fastsprout_definition__")
    if not isinstance(definition, _Definition):
        raise TypeError(
            "Use a DTO class derived from a visibility base and an entity"
        )
    return definition


def _check_name(cls: type[_DTO], name: str, definition: _Definition) -> None:
    if name in cls.__fastsprout_forbidden__:
        raise AttributeError(
            f"Field {name!r} not accessible in DTO "
            f"(operations: {sorted(cls.__fastsprout_operations__)})"
        )
    if name not in definition.allowed:
        raise AttributeError(f"Unknown DTO field {name!r}")


def _copy_default(value: Any) -> Callable[[dict[str, Any]], Any]:
    return lambda _: deepcopy(value)


def _factory_default(
    factory: Callable[[], Any],
) -> Callable[[dict[str, Any]], Any]:
    return lambda _: factory()


def _model_default(field: Any) -> Callable[[dict[str, Any]], Any]:
    return lambda data: field.get_default(
        call_default_factory=True, validated_data=data
    )


def _defaults(source: type, allowed: frozenset[str]) -> dict[str, Callable]:
    model_fields = getattr(source, "model_fields", None)
    if model_fields is not None:
        return {
            name: _model_default(field)
            for name, field in model_fields.items()
            if name in allowed and not field.is_required()
        }
    if is_dataclass(source):
        return {
            field.name: _factory_default(field.default_factory)
            if field.default_factory is not MISSING
            else _copy_default(field.default)
            for field in fields(source)
            if field.name in allowed
            and (
                field.default is not MISSING
                or field.default_factory is not MISSING
            )
        }
    return {}


def _descriptor_defaults(
    descriptors: dict[str, Field],
    allowed: frozenset[str],
    defaults: dict[str, Callable],
) -> None:
    for name in allowed - defaults.keys():
        field = descriptors[name]
        if field.default_factory is not None:
            defaults[name] = _factory_default(field.default_factory)
        elif field.default is not Undefined:
            defaults[name] = _copy_default(field.default)


def _inherit_definition(cls: type[_DTO]) -> bool:
    if len(cls.__bases__) != 1:
        return False
    parent = cls.__bases__[0]
    if not is_dto_base(parent) or "__fastsprout_definition__" not in vars(
        parent
    ):
        return False
    # Descriptors check the actual owner's own metadata on class access.
    # Install it at every inheritance level, keeping the original contract.
    cls.__fastsprout_source__ = parent.__fastsprout_source__
    cls.__fastsprout_operations__ = parent.__fastsprout_operations__
    cls.__fastsprout_forbidden__ = parent.__fastsprout_forbidden__
    cls.__fastsprout_definition__ = _definition(parent)
    return True


def _derivation_bases(cls: type[_DTO]) -> tuple[type[_DTO], type]:
    if len(cls.__bases__) != 2 or not is_dto_base(cls.__bases__[0]):
        raise TypeError(
            "Declare class Name(ReadDTO | WriteDTO | ReadWriteDTO, Entity)"
        )
    mode, source = cls.__bases__
    if mode not in (ReadDTO, WriteDTO, ReadWriteDTO) or is_dto_base(source):
        raise TypeError(
            "Derive each DTO directly from a visibility base and its entity"
        )
    return mode, source


def dto[C: _DTO](cls: type[C]) -> type[C]:
    """Prepare a visibility-restricted DTO without copying field declarations.

    Called automatically when a DTO class is declared. Applying ``@dto``
    explicitly remains supported, but is unnecessary.

    Usage::

        class UserRead(ReadDTO, User): ...
        class SpecializedRead(UserRead): ...

    DTOs always use their own constructor. It checks required, unknown, and
    forbidden names at runtime, but does not validate values. Subclasses
    inherit the same fields, defaults, and visibility as their parent DTO.
    """
    if _inherit_definition(cls):
        return cls
    mode, source = _derivation_bases(cls)
    descriptors = {
        name: value
        for base in reversed(source.__mro__)
        for name, value in vars(base).items()
        if isinstance(value, Field)
    }
    operations = mode.__fastsprout_operations__
    allowed = frozenset(
        name
        for name, field in descriptors.items()
        if field.__fastsprout_ops__ & operations
    )
    defaults = _defaults(source, allowed)
    _descriptor_defaults(descriptors, allowed, defaults)
    cls.__fastsprout_source__ = source
    cls.__fastsprout_forbidden__ = frozenset(descriptors.keys() - allowed)
    cls.__fastsprout_definition__ = _Definition(
        allowed, allowed - defaults.keys(), defaults
    )
    return cls
