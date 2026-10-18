# 3. Update And Patch

<!-- example-source: examples/actions/02_action_group/02_crud_service/03_update_and_patch.py -->

Replace writable values with UPDATE or change selected fields with PATCH.
PATCH preserves omitted fields; an explicit None clears a nullable field.

## Source

```python
"""Replace writable values with UPDATE or change selected fields with PATCH.
PATCH preserves omitted fields; an explicit None clears a nullable field.
"""

import asyncio
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import BaseSchema, Field, ReadField, inject_depends
from fastsprout.data import DataR, provide_datar, sql
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY

engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
backend = sql.SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    power: Field[int] = Field(default=10)
    note: Field[str | None] = Field(default="Ready")


class HeroPatch(BaseSchema):
    power: Field[int] = Field(default=10)
    note: Field[str | None] = Field(default=None)


# A custom patch schema gives the IDE a constructor with optional fields.
# Create, read, and update use Hero.
heroes = DataS(Hero, patch=HeroPatch)


async def main() -> None:
    inject_depends.dependency_providers[DataR] = provide_datar
    try:
        async with engine.begin() as connection:
            await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

        created = await heroes.create(
            heroes.create_schema(name="Batman", power=100, note="On patrol")
        )

        # Only explicitly supplied schema fields are applied by PATCH.
        payload = heroes.patch_schema(power=101)
        patched = await heroes.patch(created.id, payload)
        print("PATCH:", patched.name, patched.power, patched.note)

        cleared = await heroes.patch(created.id, heroes.patch_schema(note=None))
        print("PATCH with None:", cleared.name, cleared.power, cleared.note)

        # UPDATE requires name and uses entity defaults for omitted defaults.
        updated = await heroes.update(
            created.id, heroes.update_schema(name="Robin")
        )
        print("UPDATE:", updated.name, updated.power, updated.note)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
PATCH: Batman 101 On patrol
PATCH with None: Batman 101 None
UPDATE: Robin 10 Ready
```
