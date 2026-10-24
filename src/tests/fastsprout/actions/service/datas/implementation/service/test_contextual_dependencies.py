from fastsprout.actions import DataS, Service, action
from fastsprout.actions.service.datas import DataSOperation
from fastsprout.core import Depends, dataclass
from fastsprout.data import DataR
from fastsprout.testing.core import then, when

from ...common import Record


@dataclass
class Actor:
    can_delete: bool


class TestContextualDependencies:
    @when("a parent action creates two different payloads")
    async def contextual_names(self, records: DataS[Record]) -> list[str]:
        names: list[str] = []

        def check(entity: Record) -> None:
            names.append(entity.name)

        service = DataS(Record, dependencies=[Depends(check)])

        @action
        async def parent() -> None:
            await service.create(Record(name="Batman"))
            await service.create(Record(name="Robin"))

        await parent()
        return names

    @then("contextual dependencies run once per payload")
    async def test_contextual_dependencies_rerun_for_each_payload(
        self, records: DataS[Record], contextual_names: list[str]
    ) -> None:
        assert contextual_names == ["Batman", "Robin"]
        assert await records.count() == 2

    @when("a nested provider is resolved during an explicit DataR operation")
    async def nested_calls(
        self, records: DataS[Record], active_datar: DataR
    ) -> list[tuple[DataSOperation, DataR]]:
        calls: list[tuple[DataSOperation, DataR]] = []
        dependency = Depends()

        async def nested(
            operation: DataSOperation, datar: DataR = dependency
        ) -> int:
            calls.append((operation, datar))
            return await records.count(datar=datar)

        marker = Depends(nested)

        def check(count: int = marker) -> None:
            assert count == 0

        service = DataS(Record, dependencies=[Depends(check)])
        await service.create(Record(name="Batman"), datar=active_datar)
        return calls

    @then("nested dependencies receive the operation and explicit DataR")
    def test_nested_dependency_receives_operation_and_explicit_datar(
        self,
        active_datar: DataR,
        nested_calls: list[tuple[DataSOperation, DataR]],
    ) -> None:
        assert nested_calls == [("create", active_datar)]

    @when(
        "two payloads resolve sync and async dependencies through one provider"
    )
    async def actor_calls(
        self, records: DataS[Record], active_datar: DataR
    ) -> tuple[list[DataR], list[Actor], list[Actor], int]:
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
        await service.create(Record(name="Batman"), datar=active_datar)
        first = contexts[:], seen[:], actors[:]
        await service.create(Record(name="Robin"), datar=active_datar)
        return *first, len(actors)

    @then("sync and async dependencies share nested async providers")
    def test_sync_and_async_dependencies_share_nested_async_providers(
        self,
        active_datar: DataR,
        actor_calls: tuple[list[DataR], list[Actor], list[Actor], int],
    ) -> None:
        contexts, seen, actors, total = actor_calls
        assert contexts == [active_datar]
        assert seen == [actors[0], actors[0]]
        assert len(actors) == 1
        assert total == 2
