from io import StringIO
from uuid import UUID

from fastsprout.core import (
    Field,
    ReadDTO,
    ReadField,
    Schema,
    WriteDTO,
    dataclass,
    typed_fields,
)
from fastsprout.data.backend.implementation import Signpost
from fastsprout.data.entity import BaseEntity, Entitieable

__all__ = [
    "DataclassEntity",
    "DataclassRead",
    "DataclassWrite",
    "FieldsEntity",
    "FieldsRead",
    "FieldsWrite",
    "SchemaEntity",
    "SchemaRead",
    "SchemaWrite",
    "TextEntity",
]


class SchemaEntity(BaseEntity[UUID]):
    name: Field[str]


class TextEntity(BaseEntity[UUID, StringIO]):
    __signpost__ = Signpost(StringIO)
    name: Field[str]


@dataclass
class DataclassEntity(Entitieable[UUID, None], Schema):
    id: ReadField[UUID]
    name: Field[str]


@typed_fields
class FieldsEntity(Entitieable[UUID, None], Schema):
    id: ReadField[UUID]
    name: Field[str]

    def __init__(self, id: UUID, name: str) -> None:
        self.id = id
        self.name = name


class SchemaRead(ReadDTO, SchemaEntity): ...


class SchemaWrite(WriteDTO, SchemaEntity): ...


class DataclassRead(ReadDTO, DataclassEntity): ...


class DataclassWrite(WriteDTO, DataclassEntity): ...


class FieldsRead(ReadDTO, FieldsEntity): ...


class FieldsWrite(WriteDTO, FieldsEntity): ...
