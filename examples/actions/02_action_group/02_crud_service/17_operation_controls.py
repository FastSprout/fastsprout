"""Enable selected CRUD operations and override delete to archive an entity.
Operation switches also apply to overridden methods.
"""

import asyncio
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import Depends, Field, IdentificatorType, ReadField
from fastsprout.core.depends import inject_depends
from fastsprout.data import DataR, provide_datar, sql
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY

engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
backend = sql.SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    archived: Field[bool] = Field(default=False)


class HeroesService(DataS[Hero]):
    async def delete(
        self, identifier: IdentificatorType, datar: DataR = Depends()
    ) -> int:
        found = await self.get(identifier, datar=datar)
        if found is None:
            return 0
        await self.update(
            found.model_copy(update={"archived": True}), datar=datar
        )
        return 1


heroes = HeroesService()
catalog = DataS(Hero, operations=frozenset({"get", "list", "count"}))


async def main() -> None:
    inject_depends.dependency_providers[DataR] = provide_datar
    try:
        async with engine.begin() as connection:
            await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

        created = await heroes.create(heroes.create_schema(name="Batman"))

        try:
            await catalog.create(catalog.create_schema(name="Robin"))
        except AttributeError:
            print("Catalog: create disabled")

        # Changing the switch also blocks our overridden delete method.
        heroes.operations = frozenset({"get", "update"})
        try:
            await heroes.delete(created.id)
        except AttributeError:
            print("Heroes: custom delete disabled")

        heroes.operations = frozenset({"get", "update", "delete"})
        await heroes.delete(created.id)
        archived = await catalog.get(created.id)
        if archived is not None:
            print("Archived:", archived.name, archived.archived)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
