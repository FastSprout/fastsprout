from sqlmodel import Field as SQLField

from fastsprout.core import Field, ReadField
from fastsprout.data.backend.sql import SQLEntity, SQLSignpost


class CRM(SQLSignpost): ...


class ContextRecord(SQLEntity[int]):
    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str]


class CRMRecord(SQLEntity[int, CRM]):
    id: ReadField[int] = SQLField(primary_key=True)
