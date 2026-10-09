# 3. Dependencies

<!-- example-source: examples/data/01_datar/03_dependencies.py -->

Guard direct backend operations with dependencies configured on DataR.
Each dependency asks only for the arguments it needs. Access checks receive
the operation and a nested Depends provider; validation receives the entity.
Stream read checks run when the result is consumed, even after take or count.

## Source

```python
"""Guard direct backend operations with dependencies configured on DataR.
Each dependency asks only for the arguments it needs. Access checks receive
the operation and a nested Depends provider; validation receives the entity.
Stream read checks run when the result is consumed, even after take or count.
"""

import asyncio
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Field as SQLField

from fastsprout.core import Depends, Field, ReadField, dataclass
from fastsprout.data import DataR, sql
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY

engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
backend = sql.SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    power: Field[int] = Field(default=100)


@dataclass(frozen=True)
class Actor:
    can_delete: bool


async def current_actor() -> Actor:
    return Actor(can_delete=False)


def check_access(
    operation: str,
    actor: Actor = Depends(current_actor),
) -> None:
    if operation == "delete" and not actor.can_delete:
        raise PermissionError("Deleting is forbidden")
    print("Allowed:", operation)


def validate_entity(entity: Hero | None = None) -> None:
    # Reads supply a query instead of an entity, so this parameter is optional.
    if entity is not None and entity.power < 0:
        raise ValueError("Power must be non-negative")


datar = DataR(dependencies=[Depends(check_access), Depends(validate_entity)])


async def main() -> None:
    try:
        async with engine.begin() as connection:
            await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

        async with datar:
            ability = datar.ability(Hero)
            try:
                await ability.create(Hero(name="Robin", power=-1))
            except ValueError as error:
                print("Rejected:", error)

            created = await ability.create(Hero(name="Batman"))
            print("Created:", created.name)

            stream = datar.stream(sql.SQLQuery(entity=Hero)).take(1)
            print("Stream ready; read check has not run yet")
            count = await stream.count()
            print("Count:", count)

            try:
                await ability.delete(created)
            except PermissionError as error:
                print("Rejected:", error)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
Allowed: create
Rejected: Power must be non-negative
Allowed: create
Created: Batman
Stream ready; read check has not run yet
Allowed: read
Count: 1
Rejected: Deleting is forbidden
```
