from typing import TYPE_CHECKING

from .action import BaseAction, BaseActionGroup, BaseTriggerAction
from .context import Context
from .decorators import (
    hidden_lazy_await,
    lazy_await,
    typed_dataclass,
    typed_fields,
    typed_pyd_dataclass,
)
from .depends import DependencyInjector, Depends, inject_depends
from .dto import (
    ExtraReadDTO,
    ExtraReadWriteDTO,
    ExtraWriteDTO,
    ReadDTO,
    ReadWriteDTO,
    WriteDTO,
    derive_read_dto,
    derive_read_write_dto,
    derive_write_dto,
    dto,
)
from .exceptions import BaseFastSproutError, FastSproutError
from .fields import (
    EntityVisibility,
    ExtraReadField,
    ExtraWriteField,
    Field,
    InternalField,
    ReadField,
    WriteField,
)
from .schema import BaseSchema, Schema
from .types.identificable import (
    IdentificatorType,
    IDType,
    PublicIDType,
)
from .types.undefined import Undefined, UndefinedType

__all__ = [
    "BaseAction",
    "BaseActionGroup",
    "BaseFastSproutError",
    "BaseSchema",
    "BaseTriggerAction",
    "Context",
    "DependencyInjector",
    "Depends",
    "EntityVisibility",
    "ExtraReadDTO",
    "ExtraReadField",
    "ExtraReadWriteDTO",
    "ExtraWriteDTO",
    "ExtraWriteField",
    "FastSproutError",
    "Field",
    "IDType",
    "IdentificatorType",
    "InternalField",
    "PublicIDType",
    "ReadDTO",
    "ReadField",
    "ReadWriteDTO",
    "Schema",
    "Undefined",
    "UndefinedType",
    "WriteDTO",
    "WriteField",
    "dataclass",
    "derive_read_dto",
    "derive_read_write_dto",
    "derive_write_dto",
    "dto",
    "hidden_lazy_await",
    "inject_depends",
    "lazy_await",
    "typed_dataclass",
    "typed_fields",
    "typed_pyd_dataclass",
]

if TYPE_CHECKING:
    from .decorators import typed_dataclass as dataclass
else:
    dataclass = typed_dataclass
