# 3. Nested Joins

<!-- example-source: examples/data/02_stream/03_nested_joins.py -->

Compose a SQL join with another stream or an already joined stream.

Employees share one SQLSignpost, so the field join runs in SQL. Further
joins use Python key functions and the same DataR context. Building any
of these plans does not execute a query; async iteration starts the reads.

## Source

```python
"""Compose a SQL join with another stream or an already joined stream.

Employees share one SQLSignpost, so the field join runs in SQL. Further
joins use Python key functions and the same DataR context. Building any
of these plans does not execute a query; async iteration starts the reads.
"""

import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLField

from fastsprout.core import Field, ReadField
from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLEntity, SQLQuery
from fastsprout.data.backend.sql.entity import SQLSignpost


class Employee(SQLEntity[int]):
    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str]
    team_id: Field[int]


class Team(SQLEntity[int]):
    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str]


async def main() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Employee.__table__.create)
            await connection.run_sync(Team.__table__.create)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        Employee.__signpost__ = SQLSignpost(factory)
        Team.__signpost__ = Employee.__signpost__
        async with factory() as session:
            session.add_all(
                [
                    Employee(id=1, name="Ada", team_id=10),
                    Employee(id=2, name="Lin", team_id=10),
                    Team(id=10, name="Platform"),
                ]
            )
            await session.commit()

        async with DataR() as data:
            employees = data.stream(SQLQuery(Employee))
            members = employees.join(
                data.stream(SQLQuery(Team)), on=(Employee.team_id, Team.id)
            )
            # Adding one employee produces a flat three-item tuple.
            chained = members.join(
                employees,
                on=(lambda row: row[1].id, lambda person: person.team_id),
            )
            # A joined source remains a pair inside the resulting tuple.
            nested = members.join(
                members,
                on=(lambda row: row[1].id, lambda row: row[1].id),
            )

            async for employee, team, colleague in chained:
                if employee.id < colleague.id:
                    print(
                        f"Chain: {employee.name}, {colleague.name} ({team.name})"
                    )

            async for employee, team, (colleague, colleague_team) in nested:
                if employee.id < colleague.id:
                    print(
                        f"Nested: ({employee.name}, {team.name}) + "
                        f"({colleague.name}, {colleague_team.name})"
                    )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
Chain: Ada, Lin (Platform)
Nested: (Ada, Platform) + (Lin, Platform)
```
