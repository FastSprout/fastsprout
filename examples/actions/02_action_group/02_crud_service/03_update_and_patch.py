"""Replace writable values with UPDATE or change selected fields with PATCH.
PATCH preserves omitted fields; an explicit None clears a nullable field.
"""

import asyncio
from uuid import UUID, uuid4

from common import backend, database
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import BaseSchema, Field, ReadField
from fastsprout.data import sql


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
    async with database():
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


if __name__ == "__main__":
    asyncio.run(main())
