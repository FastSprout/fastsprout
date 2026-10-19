import pytest

from fastsprout.actions import DataS, Service, action
from fastsprout.core import Depends, IdentificatorType, dataclass
from fastsprout.data import DataR
from fastsprout.testing.core import when_then

from ...common import Record, RecordCreate


@dataclass
class Actor:
    can_delete: bool


class TestDependencyValidation:
    @when_then("dependencies check and normalize the payload in order")
    async def test_dependencies_run_checks_and_normalization_in_order(
        self,
        records: DataS[Record],
    ) -> None:
        calls: list[str] = []

        async def normalize(
            entity: RecordCreate,
        ) -> None:
            calls.append("model")
            entity.name = entity.name.strip()

        def check_name(entity: RecordCreate) -> None:
            calls.append("name")
            assert entity.name == " Batman "

        async def check_database(datar: DataR) -> None:
            calls.append("database")
            assert await records.count(datar=datar) == 0

        service = DataS(
            Record,
            create=RecordCreate,
            dependencies=[
                Depends(check_name),
                Depends(check_database),
                Depends(normalize),
            ],
        )
        async with DataR() as datar:
            created = await service.create(
                RecordCreate(name=" Batman "), datar=datar
            )
            assert created.name == "Batman"
            assert calls == ["name", "database", "model"]
            assert await records.count(datar=datar) == 1

    @when_then(
        "a rejected dependency stops execution and rolls back its writes"
    )
    @pytest.mark.parametrize("related", [False, True])
    async def test_dependency_failure_rolls_back_the_invocation(
        self, records: DataS[Record], related: bool
    ) -> None:
        calls: list[str] = []

        async def prepare(datar: DataR) -> None:
            calls.append("prepare")
            if related:
                await records.create(Record(name="Related"), datar=datar)

        async def reject() -> None:
            calls.append("reject")
            raise PermissionError("Forbidden")

        def after_rejection() -> None:
            calls.append("after")

        service = DataS(
            Record,
            dependencies=[
                Depends(prepare),
                Depends(reject),
                Depends(after_rejection),
            ],
        )
        with pytest.raises(PermissionError, match="Forbidden"):
            await service.create(Record(name="Batman"))
        assert calls == ["prepare", "reject"]
        assert await records.count() == 0

    async def test_delete_dependencies_receive_the_key_and_can_reject(
        self,
        records: DataS[Record],
    ) -> None:
        # given
        created = await records.create(Record(name="Batman"))
        calls: list[tuple[IdentificatorType, DataR]] = []

        async def check_exists(
            identifier: IdentificatorType, /, *, datar: DataR
        ) -> None:
            assert await records.exists(identifier, datar=datar)

        @action(dependencies=[Depends(check_exists)])
        async def check_key(
            identifier: IdentificatorType, *, datar: DataR = Depends()
        ) -> None:
            calls.append((identifier, datar))

        @action
        async def reject() -> None:
            raise PermissionError("Cannot delete")

        service = DataS(
            Record, dependencies=[check_key.dependency, Depends(reject)]
        )
        # when
        async with DataR() as datar:
            with pytest.raises(PermissionError, match="Cannot delete"):
                await service.delete(created.id, datar=datar)
        # then
        assert calls == [(created.id, datar)]
        assert await records.exists(created.id)

    async def test_sync_and_async_dependencies_share_nested_async_providers(
        self,
        records: DataS[Record],
    ) -> None:
        # given
        actors: list[Actor] = []
        contexts: list[DataR] = []
        seen: list[Actor] = []

        async def current_actor() -> Actor:
            actor = Actor(can_delete=True)
            actors.append(actor)
            return actor

        dependency = Depends(current_actor)

        def check_permission(actor: Actor = dependency) -> None:
            seen.append(actor)
            assert actor is actors[-1]

        @action
        async def check_account(
            datar: DataR, actor: Actor = dependency
        ) -> None:
            contexts.append(datar)
            seen.append(actor)
            assert actor is actors[-1]

        class AccountChecks(Service):
            account = check_account

        checks = AccountChecks()
        service = DataS(
            Record,
            dependencies=[
                Depends(current_actor),
                Depends(check_permission),
                checks.account.dependency,
            ],
        )
        # when / then
        async with DataR() as datar:
            await service.create(Record(name="Batman"), datar=datar)
            assert contexts == [datar]
            assert seen == [actors[0], actors[0]]
            assert len(actors) == 1
            await service.create(Record(name="Robin"), datar=datar)
        assert len(actors) == 2
