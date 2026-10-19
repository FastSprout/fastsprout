from enum import StrEnum
from functools import partial
from operator import attrgetter
from typing import Annotated, ClassVar
from uuid import UUID, uuid4

from pydantic import Field as PydanticField
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlmodel import Field as SQLField

from fastsprout.actions.service.datas import DataSOperation, Page
from fastsprout.core import (
    BaseSchema,
    Field,
    IdentificatorType,
    InternalField,
    ReadDTO,
    ReadField,
    Schema,
    Undefined,
    UndefinedType,
    WriteDTO,
    WriteField,
    dataclass,
)
from fastsprout.core.dto.conversion import supplied_names
from fastsprout.core.types import AnyIterable
from fastsprout.data import DataR, Relationship, SimpleAsyncEntityStream, sql
from fastsprout.data.capabilities.query import (
    And,
    BaseQuery,
    Eq,
    Expression,
    Filter,
    Gt,
    Gte,
    In,
    Lt,
    Lte,
    Ne,
    Or,
)
from fastsprout.data.capabilities.query.predicate import evaluate
from fastsprout.data.entity import Entitieable, Signpostable
from fastsprout.data.streams.protocols import AsyncEntityStream
from fastsprout.data.utils.iterable import achain

FILTER_CASES: tuple[tuple[Filter[int], set[int]], ...] = (
    (Eq(20), {20}),
    (Ne(20), {30, 40}),
    (Gt(20), {30, 40}),
    (Gte(20), {20, 30, 40}),
    (Lt(30), {20}),
    (Lte(30), {20, 30}),
    (In([20, 40]), {20, 40}),
    (In([]), set()),
    (And(Gte(20), Lt(40)), {20, 30}),
    (Or(Eq(20), And(Gte(30), Lt(40))), {20, 30}),
    (And(), {20, 30, 40}),
    (Or(), set()),
)


class LimitedPage[R](Page[R]):
    limit: Annotated[int | None, PydanticField(ge=0, le=1000)] = 1


class Status(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Record(sql.SQLEntity[UUID]):
    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    score: Field[int] = Field(default=10)
    note: Field[str | None] = Field(default="kept")
    status: Field[Status] = Field(default=Status.ACTIVE)
    password: WriteField[str] = WriteField(default="initial")
    system_key: InternalField[str] = InternalField(default="system")


class RecordRead(ReadDTO, Record):
    def label(self) -> str:
        return self.name.upper()


class RecordWrite(WriteDTO, Record): ...


class RecordCreate(BaseSchema):
    name: str
    score: int = 10


class RecordUpdate(BaseSchema):
    name: str
    score: int
    note: str | None = "replacement default"
    status: Status = Status.ACTIVE
    password: str = "changed"


class RecordPatch(BaseSchema):
    name: str | None = None
    score: int = 999
    note: str | None = None


class RecordValidation:
    def __init__(self) -> None:
        self.calls: list[tuple[DataSOperation, DataR, frozenset[str]]] = []

    async def __call__(
        self,
        operation: DataSOperation,
        datar: DataR,
        entity: Record | RecordCreate | IdentificatorType | None = None,
        data: RecordUpdate | RecordPatch | None = None,
        entities: AnyIterable[Record] = (),
    ) -> None:
        payload = data if data is not None else entity
        inputs = (
            [payload]
            if isinstance(
                payload, (Record, RecordCreate, RecordUpdate, RecordPatch)
            )
            else entities
        )
        async for item in achain(inputs):
            self.calls.append(
                (operation, datar, frozenset(supplied_names(item)))
            )
            if "score" in supplied_names(item) and item.score < 0:
                raise ValueError("Score must be non-negative")
            if "name" in supplied_names(item) and item.name is not None:
                item.name = item.name.strip()


@dataclass(kw_only=True)
class MemoryRecord(Entitieable[UUID]):
    __signpost__: ClassVar[Signpostable[None]]

    id: ReadField[UUID] = ReadField(default_factory=uuid4)
    name: Field[str]
    score: Field[int] = Field(default=10)
    password: WriteField[str] = WriteField(default="initial")
    system_key: InternalField[str] = InternalField(default="system")


@dataclass
class MemoryCreate(Schema):
    name: str


@dataclass
class MemoryPatch(Schema):
    score: int


class MemoryQuery(BaseQuery[MemoryRecord, str]):
    def build(self) -> str:
        return self.statement or ""


class MemoryAbility:
    entity: type[MemoryRecord] = MemoryRecord

    def __init__(self) -> None:
        self.items: dict[UUID, MemoryRecord] = {}
        self.contexts: list[DataR] = []

    def query_for(
        self, entity: type[MemoryRecord] | UndefinedType = Undefined
    ) -> MemoryQuery:
        source = self.entity if isinstance(entity, UndefinedType) else entity
        assert source is self.entity
        return MemoryQuery(source)

    def stream(self, query: MemoryQuery) -> AsyncEntityStream[MemoryRecord]:
        assert query.entity is self.entity
        condition: Expression[MemoryRecord] = And(*query.conditions)
        stream = SimpleAsyncEntityStream(
            [
                entity
                for entity in self.items.values()
                if query.statement is None or entity.name == query.statement
            ]
        ).filter(partial(evaluate, condition))
        for name, reverse in reversed(query.effective_orderings):
            stream = stream.sort(attrgetter(name), reverse=reverse)
        stream = stream.drop(query.offset_value)
        return (
            stream.take(query.limit_value)
            if isinstance(query.limit_value, int)
            else stream
        )

    async def find_first(self, query: MemoryQuery) -> MemoryRecord | None:
        return await self.stream(query).first()

    async def create(self, entity: MemoryRecord) -> MemoryRecord:
        self.items[entity.id] = entity
        return entity

    async def bulk_create(
        self, entities: AnyIterable[MemoryRecord]
    ) -> list[MemoryRecord]:
        return [await self.create(entity) async for entity in achain(entities)]

    async def update(self, entity: MemoryRecord) -> MemoryRecord:
        self.items[entity.id] = entity
        return entity

    async def bulk_update(
        self, entities: AnyIterable[MemoryRecord]
    ) -> list[MemoryRecord]:
        return [await self.update(entity) async for entity in achain(entities)]

    async def delete(self, entity: MemoryRecord) -> int:
        return int(self.items.pop(entity.id, None) is not None)

    async def bulk_delete(self, entities: AnyIterable[MemoryRecord]) -> int:
        deleted = 0
        async for entity in achain(entities):
            deleted += await self.delete(entity)
        return deleted


class League(sql.SQLEntity[UUID]):
    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]


class Team(sql.SQLEntity[UUID]):
    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    league: Field[League | None] = Relationship()


class TeamRecord(sql.SQLEntity[UUID]):
    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    team: Field[Team | None] = Relationship()


def loaded_query[E: sql.SQLEntity](
    source: type[E], key: UUID
) -> sql.SQLQuery[E]:
    return sql.SQLQuery(
        source,
        statement=select(source)
        .where(source.__table__.c.id == key)
        .options(selectinload("*")),
    )
